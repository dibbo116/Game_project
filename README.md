Brain Quest
Project Overview
This is a web-based game application designed to facilitate educational interactions between teachers and students. Teachers can create, manage, and assign questions for students to attempt. Students can view and attempt the assignments, with multiple-choice questions displayed one at a time.

The application is built using Flask as the backend framework, MySQL for the database, and HTML/CSS for the frontend.

Features
User Roles

Teachers can log in to create assignments and manage questions.

Students can view available assignments, attempt them and play games.

User Authentication

Registration and Login: Users can register as students or teachers. Secure login/logout functionality is provided.

Teacher Profile:

Teacher can check their profile by clicking Profile button.

Teacher and Student Dashboard:

Teacher Dashboard: Teacher can see the dashboard when they login into the system.

Student Dashboard: Student can see the dashboard when they login into the system.

Assignment Management (Teacher)

Create, Edit, and Delete Assignments: Teachers can manage assignments and add questions with difficulty levels.

Add Questions: Teachers can add multiple questions to assignments, which students later attempt.

Hint: Teacher can add hint on each question while creating an assignment.

Question Management (Teacher)

Create, Edit, and Delete Questions: Teachers can view, add, edit, and delete questions.

Hint and Difficulty set: Questions are categorized based on difficulty, and each question has an associated correct answer and can also add hint.

Student Interaction

View Assignments: Students can see all assignments.

Attempt Assignments: Students answer questions one-by-one in a multiple-choice format.

Play: Student can play arithmetic game by clicking play.

Hint: They can use hint on each question if hint is provided by the teacher.

Reporting

Track Student Progress (Student): Student can view their progress both for play and assignment.

Track Student Report (Teacher): Teacher can be each individual student’s assignment report and play game report.

Technologies Used
Backend: Flask (Python web framework)
Frontend: HTML, CSS
Database: MySQL

Step-by-Step Guide to Running the Solution

Prerequisites

To run the application, you need:

· Python: Version 3.x

· MySQL Server: For database storage

· Flask: Install via pip (pip install flask)

· XAMPP: For managing the MySQL server on localhost

Installing Required Packages

1. Clone the Repository: Download the project files from GitHub (git clone https://github.com/dibbo116/Game_project.git) Or the provided source.

2. Navigate to the Project Directory: Open a terminal or command prompt and navigate to the project’s root directory.

3. Install Dependencies: Run the following command to install all required packages:

pip install -r requirements.txt

 Setting Up the Database

1. Create the Database:

o Open your MySQL interface (e.g., phpMyAdmin or MySQL CLI).

o Create a database called game:

CREATE DATABASE game;

o Import the SQL schema from database(db_setup.sql) to create necessary tables

2. Configure Database Connection: Update app.py with your database credentials:

db_connection = mysql.connector.connect(

host="localhost",

user="root",

password="",

database="game"

)

Running the Application

1. Start the Flask Server: In the terminal, run:

python app.py

2. Access the Application: Open a web browser and navigate to http://127.0.0.1:5000.
