from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pdfkit
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = "secret123"
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# DB INIT
def init_db():
    conn = sqlite3.connect('database.db')
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

# HOME
@app.route('/')
def home():
    return render_template('index.html')

# SIGNUP
@app.route('/signup', methods=['GET','POST'])
def signup():
    error = None
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        c = request.form['confirm']

        if p != c:
            error = "Passwords do not match"
            return render_template('signup.html', error=error)

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html', error=error)

# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        photo = request.files['photo']

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

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO resumes 
    (user_id,name,email,phone,skills,projects,education,achievements,hobbies,photo)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    """, data)

    conn.commit()
    conn.close()

    return redirect('/preview')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# FORM
@app.route('/form', methods=['GET','POST'])
def form():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = (
            session['user_id'],
            request.form['name'],
            request.form['email'],
            request.form['phone'],
            request.form['skills'],
            request.form['projects'],
            request.form['education'],
            request.form['achievements'],
            request.form['hobbies']
        )

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO resumes (user_id,name,email,phone,skills,projects,education,achievements,hobbies)
        VALUES (?,?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        return redirect('/preview')

    return render_template('form.html')

# PREVIEW
@app.route('/preview')
def preview():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row   # ✅ IMPORTANT
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM resumes 
    WHERE user_id=? 
    ORDER BY id DESC LIMIT 1
    """, (session['user_id'],))

    data = cur.fetchone()
    conn.close()

    return render_template('preview.html', data=data)

# PDF DOWNLOAD
@app.route('/download')
def download():
    if 'user_id' not in session:
        return redirect('/login')

    import os

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM resumes 
    WHERE user_id=? ORDER BY id DESC LIMIT 1
    """, (session['user_id'],))

    data = cur.fetchone()
    conn.close()

    rendered = render_template('preview.html', data=data)

    path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=path)

    file_path = os.path.abspath("resume.pdf")

    pdfkit.from_string(
        rendered,
        file_path,
        configuration=config,
        options={
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'encoding': "UTF-8"
        }
    )

    return send_file(file_path, as_attachment=True)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)