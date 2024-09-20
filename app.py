from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import hashlib
from flask import flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'


# MySQL Database Connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="game"
)

# Cursor for database operations
cursor = db_connection.cursor(dictionary=True)

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        role = request.form['role']

        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        db_connection.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

## Modify the Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid Credentials')
    return render_template('login.html')

# Student Dashboard Route
@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can access this page!')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

# Teacher Dashboard Route
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can access this page!')
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html')
# Teacher Reports Route
@app.route('/reports')
def reports():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can view reports!')
        return redirect(url_for('login'))
    
    # Fetch student progress data
    cursor.execute("""
        SELECT u.username, COUNT(s.id) AS total_questions, SUM(s.score) AS correct_answers
        FROM scores s
        JOIN users u ON s.user_id = u.id
        GROUP BY u.username
    """)
    report_data = cursor.fetchall()
    
    return render_template('reports.html', report_data=report_data)
# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out successfully!')
    return redirect(url_for('home'))

# Route to view all questions (Teacher dashboard)
@app.route('/questions')
def questions():
    cursor.execute("SELECT * FROM questions")
    questions_list = cursor.fetchall()
    return render_template('questions.html', questions=questions_list)

# Route to add a question
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        answer = request.form['answer']
        difficulty = request.form['difficulty']

        cursor.execute("INSERT INTO questions (question_text, answer, difficulty) VALUES (%s, %s, %s)", 
                       (question_text, answer, difficulty))
        db_connection.commit()
        flash('Question added successfully!')
        return redirect(url_for('questions'))
    return render_template('add_question.html')

# Route to delete a question
@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
    db_connection.commit()
    flash('Question deleted successfully!')
    return redirect(url_for('questions'))

import random

# Route for the game (question answering)
@app.route('/play', methods=['GET', 'POST'])
def play():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can play the game!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        question_id = request.form['question_id']
        user_answer = request.form['answer']

        # Fetch the correct answer for the question
        cursor.execute("SELECT answer FROM questions WHERE id = %s", (question_id,))
        correct_answer = cursor.fetchone()['answer']

        # Check if the answer is correct
        if int(user_answer) == correct_answer:
            flash('Correct! Well done!', 'correct')
            score = 1
        else:
            flash('Incorrect! Try again.', 'incorrect')
            score = 0

        # Insert the result into the scores table
        cursor.execute("INSERT INTO scores (user_id, question_id, score) VALUES (%s, %s, %s)", 
                       (session['user_id'], question_id, score))
        db_connection.commit()

    # Get a random question for the game
    cursor.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 1")
    question = cursor.fetchone()

    # Generate multiple-choice options (3 random incorrect options + 1 correct option)
    correct_answer = question['answer']
    options = [correct_answer]

    # Generate 3 random incorrect answers
    while len(options) < 4:
        random_option = random.randint(correct_answer - 10, correct_answer + 10)
        if random_option != correct_answer and random_option not in options:
            options.append(random_option)

    # Shuffle options
    random.shuffle(options)
    
    return render_template('play.html', question=question, options=options)

# Route to view student progress
@app.route('/progress')
def progress():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can view progress!')
        return redirect(url_for('login'))

    # Fetch scores for the logged-in student
    cursor.execute("""
        SELECT q.question_text, s.score
        FROM scores s
        JOIN questions q ON s.question_id = q.id
        WHERE s.user_id = %s
    """, (session['user_id'],))
    scores = cursor.fetchall()

    # Calculate total and correct answers
    total_questions = len(scores)
    correct_answers = sum(score['score'] for score in scores)

    return render_template('progress.html', scores=scores, total_questions=total_questions, correct_answers=correct_answers)


if __name__ == '__main__':
    app.run(debug=True)
