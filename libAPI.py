import json
from flask import Flask, render_template, redirect, session
from flask import request
from flask_session import Session
# from datetime import timedelta
import sqlite3

app = Flask('Flask Lab')

# #creating Session class instance for handling sessions
# sesClass = Session()


class LibraryAPI(Flask):
    ADMIN = False
    _database = None
    _session = None

    def __init__(self, name: str = "Flask'a'lab"):
        super().__init__(name)

    def run(self):
        Loader(self.database)

    @property
    def database(self, config: str = "config\configuration.json"):
        if not self._database:
            self._database = json.load(config)["database"]
        return self._database

    @property
    def session(self):
        if not self._session:
            self._session = Session()
        return self._session


class Loader:
    commands = {
        "books": "SELECT * FROM books",
        "people": "SELECT userid, username FROM users",
        "person": "SELECT * FROM users WHERE userid={}"
    }
    db_name = "database.db"

    def __init__(self, db_name):
        self.db_name = db_name

#     @staticmethod
#     def connection(function: Function, db_name: str):
#         con = sqlite3.connect(db_name)
#         cur = con.cursor()
#         def command():
#             return function(cur)
#         con.close()
#         return command()
#     @connection(db_name)
#     def load(cursor: sqlite3.Cursor, command: str, id: int=None):
#         if id==None:
#             cursor.execute(command)
#             books = cursor.fetchall()
#         else:
#             cursor.execute(command.format(id))
#             books = cursor.fetchall()
#         return books

    # function for loading books from database
    def load_books(self):
        con = sqlite3.connect(self.DATABASE)
        cur = con.cursor()
        cur.execute("SELECT * FROM books")
        books = cur.fetchall()
        con.close()
        return books

    def load_people(self):
        con = sqlite3.connect(self.DATABASE)
        cur = con.cursor()
        cur.execute("SELECT userid, username FROM users")
        users = cur.fetchall()
        con.close()
        return users

    def load_person(self, id: int):
        con = sqlite3.connect(self.DATABASE)
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE userid = " + str(id))
        user = cur.fetchall()
        con.close()
        return user

    # function that handles get requests to / directory
    @app.route('/', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
    def indexGet(self):
        if 'user' in session:
            books = self.load_books()
            return render_template('index.html', books=books, admin=admin)
        else:
            return redirect("/login")

    # function that handles post requests to / directory
    @app.route('/', methods=['POST'])
    def indexPost(self):
        if 'user' in session:
            response_form = request.form
            if response_form["author"] != "" and response_form["title"] != "":

                con = sqlite3.connect(self.DATABASE)
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
                    books = self.load_books()
                    redirect("/")
                    return render_template(
                        'index.html',
                        books=books,
                        message="book added",
                        admin=admin
                    )
                else:
                    books = self.load_books()
                    redirect("/")
                    return render_template(
                        'index.html',
                        books=books,
                        message="book already in the database!",
                        admin=admin
                    )
            else:
                books = self.load_books()
                redirect("/")
                return render_template(
                    'index.html',
                    books=books,
                    message="author and title cannot be empty!",
                    admin=admin
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
    def loginPost(self):
        if 'user' not in session:
            response_form = request.form
            print(response_form)
            con = sqlite3.connect(self.DATABASE)
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
                global admin
                admin = user[0][3]
                return redirect('/')
        else:
            return redirect("/")

    # function for handling database (uncomment and use localhost:5000/dbcreate to create a usable database)
    # @app.route('/dbcreate')
    # def dbcreate():
    #     # Db connection
    #     conn = sqlite3.connect(DATABASE)
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
            global admin
            admin = False
            session.pop('user')
            return render_template('logout.html')
        else:
            # Redirect the client to the homepage
            return redirect('/')

    # function that handles get requests to /users
    @app.route('/users', methods=['GET', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'CONNECT'])
    def users():
        if 'user' in session:
            if admin == 1:
                users = load_people()
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
            if admin == 1:
                response_form = request.form
                if response_form["login"] != "" and response_form["password"] != "":
                    con = sqlite3.connect(DATABASE)
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
                        users = load_people()
                        return render_template('users.html', message="user added", users=users)
                    else:
                        users = load_people()
                        redirect("/users")
                        return render_template('users.html', message="such user already exists!", users=users)
                else:
                    users = load_people()
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
            if admin == 1:
                user = load_person(id)
                return render_template('user.html', user=user)
            else:
                return redirect('/')
        else:
            # Redirect the client to the homepage
            return redirect('/')

# #on lab3.py startup
# if __name__ == '__main__':
#     app.secret_key = 'super secret key'
#     app.config['SESSION_TYPE'] = 'filesystem'
#     app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=5)
#     sesClass.init_app(app)
#     app.config.from_object(__name__)
#     app.run(debug=True)
    