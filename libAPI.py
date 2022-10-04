import json
import logging
from flask import Flask, render_template, redirect, session
from flask import request
from flask_session import Session
from datetime import timedelta
import sqlite3


class Error(Exception):
    info = "Error occured while making connection: {}"


class MissingDataBaseNameError(Exception):
    info = Error.info.format("Missing Database name")


class LibraryAPI(Flask):
    _database = None
    _session = None
    _loader = None

    def __init__(self, name: str = "Flask'a'lab"):
        super().__init__(name)
        self.admin = False

    @property
    def loader(self):
        if not self._loader:
            self._loader = Loader(self.database)
        return self._loader

    @property
    def database(self, config: str = r"config\configuration.json"):
        if not self._database:
            with open(config, "r") as f:
                data = json.load(f)
            self._database = data["DATABASE"]
        return self._database

    @property
    def session(self):
        if not self._session:
            self._session = Session()
        return self._session

    def load(self, command: str, *args):
        return self.loader.load(command, *args)

    def insert(self, command: str, *args):
        return self.loader.insert(command, *args)

    def prepare_request(
            self,
            command: str,
            template: str,
            message: str = None,
            redirect: bool = False,
            path: str = '/',
            **kwargs
            ):

        result = self.load(command)

        if redirect:
            redirect(path)

        return render_template(
            template,
            books=result,
            message=message,
            admin=app.admin,
            **kwargs
        )

    def prepare_index(
            self,
            message: str = '',
            redirect: bool = False,
            path: str = '/'
            ):
        return self.prepare_request(
            command="books",
            template="index.html",
            message=message,
            redirect=redirect,
            path=path
        )


class Loader:
    def __init__(self, db_name):
        self.db_name = db_name
        self.commands = {
            "books": "SELECT * FROM books",
            "people": "SELECT userid, username FROM users",
            "person": "SELECT * FROM users WHERE userid={}",
            "books_with_author_and_title":
                "SELECT * FROM books where author = '{}' and title = '{}' LIMIT 1",
            "check_if_book_in_db":
                "INSERT INTO books (author,title) VALUES ('{}','{}')",
            "user_login":
                "SELECT * FROM users where username='{}' and password='{}' LIMIT 1",
            "get_user":
                "SELECT * FROM users where username = '{}' LIMIT 1",
            "add_user":
                "INSERT INTO users (username, password, admin) VALUES ('{}','{}','{}')"
        }

    @staticmethod
    def connect(db_name):
        try:
            con = sqlite3.connect(db_name)
        except sqlite3.Error:
            logging.error(
                Error.info.format(' '.join(["Error occured for:", db_name]))
            )
            exit(1)
        return con

    def insert(self, command: str, *args):
        if self.commands.get(command, None):
            command = self.commands[command]
            if not args:
                return self.run_command(command, insert=True)
            return self.run_command(command, *args, insert=True)
        else:
            raise AttributeError("Command needs to match the allowed list")

    def load(self, command: str, *args):
        if self.commands.get(command, None):
            command = self.commands[command]
            if not args:
                return self.run_command(command)
            return self.run_command(command, *args)
        else:
            raise AttributeError("Command needs to match the allowed list")

    def run_command(self, command: str, *args, insert: bool = False):
        if not self.db_name:
            raise MissingDataBaseNameError

        if args:
            return self._execute_with_params(command, *args, insert)
        return self._execute(command, insert)

    def _execute_with_params(self, command, *args, insert: bool = False):
        with self.connect(self.db_name) as con:
            cur = con.cursor()
            print(command.format(*args))
            cur.execute(command.format(*args))
            if insert:
                return con.commit()
            return cur.fetchall()

    def _execute(self, command, insert: bool = False):
        with self.connect(self.db_name) as con:
            cur = con.cursor()
            cur.execute(command)
            if insert:
                return con.commit()
            return cur.fetchall()


app = LibraryAPI('')


# function that handles get requests to / directory
@app.route('/', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
def index_get():
    if 'user' in session:
        books = app.load("books")
        return render_template('index.html', books=books, admin=app.admin)
    else:
        return redirect("/login")


# function that handles post requests to / directory
@app.route('/', methods=['POST'])
def index_post():
    if 'user' in session:
        response_author = request.form["author"]
        response_from_title = request.form["title"]
        if response_author and response_from_title:
            books = app.load(
                "books_with_author_and_title",
                response_author,
                response_from_title
            )
            if books == []:
                app.insert(
                    "check_if_book_in_db",
                    response_author,
                    response_from_title
                )
                return app.prepare_index(
                    message="book added"
                )
            else:
                return app.prepare_index(
                    message="book already in the database"
                )
        else:
            return app.prepare_index(
                message="author and title cannot be empty!"
            )
    else:
        return redirect("/login")


# function that handles get requests to /login directory
@app.route('/login', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
def login_get():
    if 'user' not in session:
        return render_template('login.html')
    else:
        return redirect("/")


# function that handles post requests to /login directory
@app.route('/login', methods=['POST'])
def login_post():
    if 'user' not in session:
        response = request.form
        user = app.load(
            "user_login",
            response['login'],
            response['password']
        )
        if user == []:
            return render_template('login.html', message="incorrect login")
        else:
            session['user'] = response["login"]
            app.admin = user[0][3]
            return redirect('/')
    else:
        return redirect("/")


# function for handling database (uncomment and use localhost:5000/dbcreate to create a usable database)
@app.route('/dbcreate')
def create_db():
    # Db connection
    conn = sqlite3.connect(app.database)
    cur = conn.cursor()
    # Create tables with sqlite3
    conn.execute('CREATE TABLE users (userid INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, admin BOOL)')
    conn.execute('CREATE TABLE books (author TEXT, title TEXT)')
    cur.execute('INSERT INTO books (author,title) VALUES (\"Christopher Paolini\", \"Eragon\")')
    conn.commit()
    cur.execute('INSERT INTO users (username, password, admin) VALUES (\"admin\", \"admin\", True)')
    conn.commit()
    cur.execute('INSERT INTO users (username, password, admin) VALUES (\"user\", \"user\", False)')
    conn.commit()
    # Terminate the db connection#
    conn.close()
    return index_get()


# function that handles logout
@app.route('/logout')
def logout():
    # If the user session exists - remove it
    if 'user' in session:
        app.admin = False
        session.pop('user')
        return render_template('logout.html')
    else:
        # Redirect the client to the homepage
        return redirect('/')


# function that handles get requests to /users
@app.route('/users', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
def users():
    if 'user' in session:
        if app.admin == 1:
            users = app.load("people")
            return render_template('users.html', users=users)
    return redirect('/')


# function that handles post requests to /users
@app.route('/users', methods=['POST'])
def user_add():
    if 'user' in session:
        if app.admin == 1:
            response = request.form
            if response["login"] and response["password"]:
                user = app.load("get_user", response["login"])
                if user == []:
                    try:
                        adm = True if response["admin"] == 'true' else False
                    except KeyError:
                        adm = False
                    app.insert(
                        "add_user",
                        response["login"],
                        response["password"],
                        adm
                    )
                    users = app.load("people")
                    return render_template(
                        'users.html',
                        message="user added",
                        users=users
                    )
                else:
                    return app.prepare_request(
                        "people",
                        "users.html",
                        path="/users",
                        message="such user already exists!",
                        users=users
                    )
            else:
                return app.prepare_request(
                    "people",
                    "users.html",
                    path="/users",
                    message="such user already exists!",
                    users=users
                )
    return redirect('/')


# function that handles get requests to /users/<id>
@app.route('/users/<int:id>')
def user(id):
    if 'user' in session:
        if app.admin == 1:
            user = app.load("person", id)
            return render_template('user.html', user=user)
    return redirect('/')


# #on lab3.py startup
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
    app.session.init_app(app)
    app.config.from_object(__name__)
    app.run(debug=True)
