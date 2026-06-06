from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'school_result_2024'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='teacher')

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    score = db.Column(db.Float)
    grade = db.Column(db.String(5))
    term = db.Column(db.String(20))
    year = db.Column(db.String(10))
    student = db.relationship('Student', backref='results')
    subject = db.relationship('Subject', backref='results')

# --- HELPER ---
def calculate_grade(score):
    if score >= 70:
        return 'A'
    elif score >= 60:
        return 'B'
    elif score >= 50:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'

# --- ROUTES ---
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    total_students = Student.query.count()
    total_subjects = Subject.query.count()
    total_results = Result.query.count()
    return render_template('dashboard.html',
                         total_students=total_students,
                         total_subjects=total_subjects,
                         total_results=total_results)

@app.route('/students')
def students():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    all_students = Student.query.all()
    return render_template('students.html',
                         students=all_students)

@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        student_class = request.form['student_class']
        age = request.form['age']
        gender = request.form['gender']
        new_student = Student(
            name=name,
            student_class=student_class,
            age=age,
            gender=gender
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('students'))
    return render_template('add_student.html')

@app.route('/delete-student/<int:id>')
def delete_student(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    student = db.session.get(Student, id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('students'))

@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        new_subject = Subject(name=name)
        db.session.add(new_subject)
        db.session.commit()
    all_subjects = Subject.query.all()
    return render_template('subjects.html',
                         subjects=all_subjects)

@app.route('/delete-subject/<int:id>')
def delete_subject(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    subject = db.session.get(Subject, id)
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for('subjects'))

@app.route('/results', methods=['GET', 'POST'])
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    students = Student.query.all()
    subjects = Subject.query.all()
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject_id = request.form['subject_id']
        score = float(request.form['score'])
        term = request.form['term']
        year = request.form['year']
        grade = calculate_grade(score)
        new_result = Result(
            student_id=student_id,
            subject_id=subject_id,
            score=score,
            grade=grade,
            term=term,
            year=year
        )
        db.session.add(new_result)
        db.session.commit()
    all_results = Result.query.all()
    return render_template('results.html',
                         results=all_results,
                         students=students,
                         subjects=subjects)

@app.route('/report-card/<int:student_id>')
def report_card(student_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    student = db.session.get(Student, student_id)
    results = Result.query.filter_by(
        student_id=student_id
    ).all()
    total = sum(r.score for r in results)
    average = total / len(results) if results else 0
    overall_grade = calculate_grade(average)
    return render_template('report_card.html',
                         student=student,
                         results=results,
                         average=average,
                         overall_grade=overall_grade)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = db.session.execute(
            db.select(User).filter_by(username='admin')
        ).scalar_one_or_none()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)