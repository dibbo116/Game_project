from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import hashlib
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Database Connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="game"
)

# Define the directory where you want to save uploaded files
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
            db_connection.commit()

            user_id = cursor.lastrowid  # Get the newly created user ID

            # If the user is a teacher, create their profile
            if role == 'teacher':
                full_name = request.form['full_name']
                email = request.form['email']
                phone_number = request.form['phone_number']
                designation = request.form['designation']

                # Handle the profile picture upload
                profile_picture = None
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename != '':
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        profile_picture = file_path

                cursor.execute("""
                    INSERT INTO teacher_profiles (user_id, full_name, email, phone_number, designation, profile_picture)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, full_name, email, phone_number, designation, profile_picture))
                db_connection.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        with db_connection.cursor(dictionary=True) as cursor:
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

# Teacher Dashboard Route with Profile Display
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can access this page!')
        return redirect(url_for('login'))

    # Use a context manager to handle the cursor
    with db_connection.cursor(dictionary=True) as cursor:
        # Fetch the teacher's full name
        cursor.execute("SELECT full_name FROM teacher_profiles WHERE user_id = %s", (session['user_id'],))
        profile = cursor.fetchone()

    return render_template('teacher_dashboard.html', full_name=profile['full_name'])


# Route to View Teacher Profile
@app.route('/teacher_profile')
def teacher_profile():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can view this page!')
        return redirect(url_for('login'))

    # Use a context manager to handle the cursor
    with db_connection.cursor(dictionary=True) as cursor:
        # Fetch the teacher's profile information
        cursor.execute("SELECT * FROM teacher_profiles WHERE user_id = %s", (session['user_id'],))
        profile = cursor.fetchone()

    return render_template('teacher_profile.html', profile=profile)

# Route to create an assignment (teacher)
@app.route('/create_assignment', methods=['GET', 'POST'])
def create_assignment():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can create assignments!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute("INSERT INTO assignments (title, description, created_by) VALUES (%s, %s, %s)",
                           (title, description, session['user_id']))
            db_connection.commit()
            assignment_id = cursor.lastrowid  # Get the ID of the newly created assignment

        flash('Assignment created successfully!')
        return redirect(url_for('add_questions_to_assignment', assignment_id=assignment_id))

    return render_template('create_assignment.html')

# Route to manage assignments (view and add questions) for teachers
@app.route('/manage_assignments')
def manage_assignments():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can manage assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM assignments WHERE created_by = %s", (session['user_id'],))
        assignments = cursor.fetchall()

    return render_template('manage_assignments.html', assignments=assignments)


# Route for students to view assignments
@app.route('/view_assignments')
def view_assignments():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can view assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM assignments")
        assignments = cursor.fetchall()

    return render_template('view_assignments.html', assignments=assignments)
# Route to attempt an assignment question-by-question (student)
@app.route('/attempt_assignment/<int:assignment_id>/<int:question_index>', methods=['GET', 'POST'])
def attempt_assignment(assignment_id, question_index):
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can attempt assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        if request.method == 'POST':
            question_id = request.form.get('question_id')
            student_answer = request.form.get('answer')

            if question_id and student_answer:
                cursor.execute("SELECT answer FROM questions WHERE id = %s", (question_id,))
                correct_answer = cursor.fetchone()['answer']
                is_correct = int(student_answer) == correct_answer

                cursor.execute("INSERT INTO student_assignment_responses (assignment_id, question_id, user_id, student_answer, is_correct) VALUES (%s, %s, %s, %s, %s)",
                               (assignment_id, question_id, session['user_id'], student_answer, is_correct))
                db_connection.commit()

            # Move to the next question
            question_index += 1

        # Fetch the next question in the assignment
        cursor.execute("""
            SELECT q.id, q.question_text, q.answer FROM questions q
            JOIN assignment_questions aq ON q.id = aq.question_id
            WHERE aq.assignment_id = %s
            ORDER BY q.id LIMIT 1 OFFSET %s
        """, (assignment_id, question_index))
        current_question = cursor.fetchone()

        # Generate multiple-choice options if there is a question
        options = []
        if current_question:
            correct_answer = current_question['answer']
            options = [correct_answer] + random.sample(range(correct_answer - 10, correct_answer + 10), 3)
            random.shuffle(options)

    return render_template('attempt_assignment.html', current_question=current_question, options=options, assignment_id=assignment_id, question_index=question_index)

# Route to add questions to an assignment (teacher)
@app.route('/add_questions_to_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def add_questions_to_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can add questions to assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        if request.method == 'POST':
            question_text = request.form['question_text']
            answer = request.form['answer']
            difficulty = request.form['difficulty']

            # Insert the new question into the questions table
            cursor.execute("INSERT INTO questions (question_text, answer, difficulty) VALUES (%s, %s, %s)",
                           (question_text, answer, difficulty))
            question_id = cursor.lastrowid  # Get the ID of the newly created question

            # Link the question to the assignment in the assignment_questions table
            cursor.execute("INSERT INTO assignment_questions (assignment_id, question_id) VALUES (%s, %s)",
                           (assignment_id, question_id))
            db_connection.commit()

            flash('Question added to the assignment successfully!')

        # Get all questions that are already added to the assignment
        cursor.execute("""
            SELECT q.id, q.question_text, q.answer, q.difficulty FROM questions q
            JOIN assignment_questions aq ON q.id = aq.question_id
            WHERE aq.assignment_id = %s
        """, (assignment_id,))
        assignment_questions = cursor.fetchall()

    return render_template('add_questions_to_assignment.html', assignment_questions=assignment_questions, assignment_id=assignment_id)

# Route to remove a question from an assignment
@app.route('/remove_question_from_assignment/<int:question_id>/<int:assignment_id>')
def remove_question_from_assignment(question_id, assignment_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can remove questions from assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("DELETE FROM assignment_questions WHERE question_id = %s AND assignment_id = %s", (question_id, assignment_id))
        db_connection.commit()

    flash('Question removed from the assignment successfully!')
    return redirect(url_for('add_questions_to_assignment', assignment_id=assignment_id))

# Route to edit an assignment
@app.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def edit_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can edit assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            cursor.execute("UPDATE assignments SET title = %s, description = %s WHERE id = %s",
                           (title, description, assignment_id))
            db_connection.commit()
            flash('Assignment updated successfully!')
            return redirect(url_for('manage_assignments'))

        # Fetch the existing assignment details for the edit form
        cursor.execute("SELECT * FROM assignments WHERE id = %s", (assignment_id,))
        assignment = cursor.fetchone()

    return render_template('edit_assignment.html', assignment=assignment)

# Route to delete an assignment
@app.route('/delete_assignment/<int:assignment_id>')
def delete_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can delete assignments!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
        cursor.execute("DELETE FROM assignment_questions WHERE assignment_id = %s", (assignment_id,))
        db_connection.commit()

    flash('Assignment deleted successfully!')
    return redirect(url_for('manage_assignments'))

# Route to start an assignment (student)
@app.route('/start_assignment/<int:assignment_id>')
def start_assignment(assignment_id):
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can start assignments!')
        return redirect(url_for('login'))

    # Redirect to the first question in the assignment
    return redirect(url_for('attempt_assignment', assignment_id=assignment_id, question_index=0))

# Teacher Reports Route
@app.route('/reports')
def reports():
    if 'user_id' not in session or session['role'] != 'teacher':
        flash('Only teachers can view reports!')
        return redirect(url_for('login'))
    
    with db_connection.cursor(dictionary=True) as cursor:
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

# Route to View All Questions (Teacher Dashboard)
@app.route('/questions')
def questions():
    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM questions")
        questions_list = cursor.fetchall()
    return render_template('questions.html', questions=questions_list)

# Route to Add a Question
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        answer = request.form['answer']
        difficulty = request.form['difficulty']

        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute("INSERT INTO questions (question_text, answer, difficulty) VALUES (%s, %s, %s)", 
                           (question_text, answer, difficulty))
            db_connection.commit()
        flash('Question added successfully!')
        return redirect(url_for('questions'))
    return render_template('add_question.html')

# Route to Delete a Question
@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        db_connection.commit()
    flash('Question deleted successfully!')
    return redirect(url_for('questions'))

# Route for the Game (Question Answering)
@app.route('/play', methods=['GET', 'POST'])
def play():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can play the game!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        question_id = request.form['question_id']
        user_answer = request.form['answer']

        with db_connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT answer FROM questions WHERE id = %s", (question_id,))
            correct_answer = cursor.fetchone()['answer']

            score = 1 if int(user_answer) == correct_answer else 0
            flash('Correct!' if score == 1 else 'Incorrect! Try again.')

            cursor.execute("INSERT INTO scores (user_id, question_id, score) VALUES (%s, %s, %s)", 
                           (session['user_id'], question_id, score))
            db_connection.commit()

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 1")
        question = cursor.fetchone()

    correct_answer = question['answer']
    options = [correct_answer] + random.sample(range(correct_answer - 10, correct_answer + 10), 3)
    random.shuffle(options)

    return render_template('play.html', question=question, options=options)

# Route to View Student Progress
@app.route('/progress')
def progress():
    if 'user_id' not in session or session['role'] != 'student':
        flash('Only students can view progress!')
        return redirect(url_for('login'))

    with db_connection.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT q.question_text, s.score
            FROM scores s
            JOIN questions q ON s.question_id = q.id
            WHERE s.user_id = %s
        """, (session['user_id'],))
        scores = cursor.fetchall()

    total_questions = len(scores)
    correct_answers = sum(score['score'] for score in scores)

    return render_template('progress.html', scores=scores, total_questions=total_questions, correct_answers=correct_answers)

if __name__ == '__main__':
    app.run(debug=True)
