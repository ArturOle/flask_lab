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

    def load(self, command: str, id: int = None):
        return self.loader.load(command, id)


class Loader:
    def __init__(self, db_name):
        self.db_name = db_name
        self.commands = {
            "books": "SELECT * FROM books",
            "people": "SELECT userid, username FROM users",
            "person": "SELECT * FROM users WHERE userid={}"
        }

    @staticmethod
    def connect(db_name):
        try:
            con = sqlite3.connect(db_name)
        except sqlite3.Error:
            logging.error(
                Error.info.format(' '.join(["Error occured for:", db_name])))
            exit(1)
        return con

    def extract(self, command: str, id: int = None):
        if not self.db_name:
            raise MissingDataBaseNameError

        if id:
            return self._extract_with_id(command, id)
        return self._extract(command)

    def _extract_with_id(self, command, id):
        with self.connect(self.db_name) as con:
            cur = con.cursor()
            cur.execute(command.format(id))
            return cur.fetchall()

    def _extract(self, command):
        with self.connect(self.db_name) as con:
            cur = con.cursor()
            cur.execute(command)
            return cur.fetchall()

    def load(self, command: str, id: int = None):
        command = self.commands[command]
        if not id:
            return self.extract(command)
        return self.extract(command, id)

    # # function for loading books from database
    # def load_books(self):
    #     con = sqlite3.connect(self.database)
    #     cur = con.cursor()
    #     cur.execute("SELECT * FROM books")
    #     books = cur.fetchall()
    #     con.close()
    #     return books

    # def load_people(self):
    #     con = sqlite3.connect(self.database)
    #     cur = con.cursor()
    #     cur.execute("SELECT userid, username FROM users")
    #     users = cur.fetchall()
    #     con.close()
    #     return users

    # def load_person(self, id: int):
    #     con = sqlite3.connect(self.database)
    #     cur = con.cursor()
    #     cur.execute("SELECT * FROM users WHERE userid = " + str(id))
    #     user = cur.fetchall()
    #     con.close()
    #     return user


app = LibraryAPI('')


# function that handles get requests to / directory
@app.route('/', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
def indexGet():
    if 'user' in session:
        books = app.load("books")
        return render_template('index.html', books=books, admin=app.admin)
    else:
        return redirect("/login")


# function that handles post requests to / directory
@app.route('/', methods=['POST'])
def indexPost():
    if 'user' in session:
        response_form = request.form
        if response_form["author"] != "" and response_form["title"] != "":

            con = sqlite3.connect(app.database)
            # Fetch data from table
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM books where author = ? and title = ? LIMIT 1",
                (response_form['author'], response_form['title'])
            )
            books = cur.fetchall()
            if books == []:
                cur.execute(
                    "INSERT INTO books (author,title) VALUES (?,?)",
                    (response_form["author"], response_form["title"])
                )
                con.commit()
                con.close()
                books = app.load()
                redirect("/")
                return render_template(
                    'index.html',
                    books=books,
                    message="book added",
                    admin=app.admin
                )
            else:
                books = app.load()
                redirect("/")
                return render_template(
                    'index.html',
                    books=books,
                    message="book already in the database!",
                    admin=app.admin
                )
        else:
            books = app.load()
            redirect("/")
            return render_template(
                'index.html',
                books=books,
                message="author and title cannot be empty!",
                admin=app.admin
            )
    else:
        return redirect("/login")


# function that handles get requests to /login directory
@app.route('/login', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
def loginGet():
    if 'user' not in session:
        return render_template('login.html')
    else:
        return redirect("/")


# function that handles post requests to /login directory
@app.route('/login', methods=['POST'])
def loginPost():
    if 'user' not in session:
        response_form = request.form
        print(response_form)
        con = sqlite3.connect(app.database)
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM users where username=? and password=? LIMIT 1",
            (response_form['login'], response_form['password'])
        )
        user = cur.fetchall()
        if user == []:
            return render_template('login.html', message="incorrect login")
        else:
            session['user'] = response_form["login"]
            print(user)
            app.admin = user[0][3]
            return redirect('/')
    else:
        return redirect("/")

# function for handling database (uncomment and use localhost:5000/dbcreate to create a usable database)
# @app.route('/dbcreate')
# def dbcreate():
#     # Db connection
#     conn = sqlite3.connect(database)
#     cur = conn.cursor()
#     # Create tables with sqlite3
#     conn.execute('CREATE TABLE users (userid INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, admin BOOL)')
#     conn.execute('CREATE TABLE books (author TEXT, title TEXT)')
#     cur.execute('INSERT INTO books (author,title) VALUES (\"Christopher Paolini\", \"Eragon\")')
#     conn.commit()
#     cur.execute('INSERT INTO users (username, password, admin) VALUES (\"admin\", \"admin\", True)')
#     conn.commit()
#     cur.execute('INSERT INTO users (username, password, admin) VALUES (\"user\", \"user\", False)')
#     conn.commit()
#     # Terminate the db connection#
#     conn.close()
#     return indexGet()


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
        else:
            return redirect('/')
    else:
        # Redirect the client to the homepage
        return redirect('/')


# function that handles post requests to /users
@app.route('/users', methods=['POST'])
def user_add():
    if 'user' in session:
        if app.admin == 1:
            response_form = request.form
            if response_form["login"] != "" and response_form["password"] != "":
                con = sqlite3.connect(app.database)
                # Fetch data from table
                cur = con.cursor()
                print(response_form)
                cur.execute(
                    "SELECT * FROM users where username = \"" +str(response_form["login"]) + "\" LIMIT 1")
                users = cur.fetchall()
                if users == []:
                    try:
                        adm = True if response_form["admin"] == 'on' else False
                    except KeyError:
                        adm = False
                    cur.execute("INSERT INTO users (username, password, admin) VALUES (?,?,?)",
                    (response_form["login"],response_form["password"], adm))
                    con.commit()
                    con.close()
                    users = app.load("people")
                    return render_template('users.html', message="user added", users=users)
                else:
                    users = app.load("people")
                    redirect("/users")
                    return render_template('users.html', message="such user already exists!", users=users)
            else:
                users = app.load("people")
                redirect("/users")
                return render_template('users.html', message="login and password cannot be empty!", users=users)       
        else:
            return redirect('/')
    else:
        # Redirect the client to the homepage
        return redirect('/')


# function that handles get requests to /users/<id>
@app.route('/users/<int:id>')
def user(id):
    if 'user' in session:
        if app.admin == 1:
            user = app.load("person", id)
            return render_template('user.html', user=user)
        else:
            return redirect('/')
    else:
        # Redirect the client to the homepage
        return redirect('/')


# #on lab3.py startup
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
    app.session.init_app(app)
    app.config.from_object(__name__)
    app.run(debug=True)
