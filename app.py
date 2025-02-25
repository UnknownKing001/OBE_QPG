from flask import Flask, render_template, redirect, url_for, session, flash, request
from dotenv import load_dotenv
import os
from flask_mysqldb import MySQL
import bcrypt
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback_secret_key')

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')  # Set in .env
app.config['MYSQL_DB'] = 'obe_quest'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'name' in request.form:  # Sign-up
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user:
                flash('Email already exists!', 'danger')
                return redirect(url_for('login'))

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
            mysql.connection.commit()
            cursor.close()

            flash('Registration successful! Please sign in.', 'success')
            return redirect(url_for('login'))

        else:  # Sign-in
            email = request.form['email']
            password = request.form['password']

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password!', 'danger')
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    # Fetch dashboard stats
    cursor.execute("SELECT COUNT(*) as course_count FROM courses WHERE user_id=%s", (session['user_id'],))
    course_count = cursor.fetchone()['course_count']

    cursor.execute("SELECT COUNT(*) as question_count FROM questions WHERE user_id=%s", (session['user_id'],))
    question_count = cursor.fetchone()['question_count']

    cursor.execute("SELECT COUNT(*) as paper_count FROM question_papers WHERE user_id=%s", (session['user_id'],))
    paper_count = cursor.fetchone()['paper_count']

    # Fetch courses for the dropdown
    cursor.execute("SELECT id, course_name FROM courses WHERE user_id=%s", (session['user_id'],))
    courses = cursor.fetchall()

    cursor.close()

    return render_template('dashboard.html',
                          course_count=course_count,
                          question_count=question_count,
                          paper_count=paper_count,
                          courses=courses)

@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/question-bank')
def question_bank():
    return render_template('question_bank.html')

@app.route('/generate-paper')
def generate_paper():
    return render_template('qp_generate.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/add-question')
def add_question():
    return render_template('add_question.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)