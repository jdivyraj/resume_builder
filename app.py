from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = os.path.join(os.getcwd(), 'database.db')


# ================= DB INIT =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        projects TEXT,
        education TEXT,
        achievements TEXT,
        hobbies TEXT,
        photo TEXT
    )
    ''')

    conn.commit()
    conn.close()


init_db()


# ================= HOME =================
@app.route('/')
def home():
    return render_template('index.html')


# ================= SIGNUP =================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None

    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        c = request.form['confirm']

        if p != c:
            error = "Passwords do not match"
            return render_template('signup.html', error=error)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (u, p))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html', error=error)


# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            error = "Invalid credentials"

    return render_template('login.html', error=error)


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return render_template('dashboard.html')


# ================= FORM =================
@app.route('/form', methods=['GET', 'POST'])
def form():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        photo = request.files.get('photo')
        filename = None

        if photo and photo.filename != "":
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        data = (
            session['user_id'],
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['skills'],
            request.form['projects'],
            request.form['education'],
            request.form['achievements'],
            request.form['hobbies'],
            filename
        )

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO resumes 
        (user_id,name,email,phone,skills,projects,education,achievements,hobbies,photo)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        return redirect('/preview')

    return render_template('form.html')


# ================= PREVIEW =================
@app.route('/preview')
def preview():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM resumes 
    WHERE user_id=? 
    ORDER BY id DESC LIMIT 1
    """, (session['user_id'],))

    data = cur.fetchone()
    conn.close()

    return render_template('preview.html', data=data)


# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))