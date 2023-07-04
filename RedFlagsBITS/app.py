
from flask import Flask, render_template, request, url_for, redirect
from flask import send_file, send_from_directory, abort
import io
import os
from datetime import datetime
import model
import xlsxwriter as xl
from typing import Tuple
import constants
import csv
import pandas as pd
import numpy as np
import waitress 
from cs50 import SQL
import sqlite3
from flask import flash 
app = Flask(__name__)
path = str(os.path.dirname(os.path.abspath(__file__)))
path = path.replace('\\', '/')
app.config['files'] = path + '/temp/'


@app.route('/', methods=('GET', 'POST'))  # Route and accepted Methods
@app.route('/index', methods=('GET', 'POST'))
def index():
    """

    """
    header_1 = 'Red Flags'
    header_2 = 'For Back Pain'
    explanation = """
    Some cases of back pain can be serious, and require immediate medical attention.
    We are going to ask a few question to understand the nature of your pain.
    """
    return render_template('index.html', header_1=header_1, header_2=header_2, explanation=explanation)

@app.route('/red_flags', methods=('GET', 'POST'))
@app.route('/red_flags/<int:question_number>', methods=('GET', 'POST'))
def red_flags_questionnaire(question_number: int = 0):
    num_question = 3
    header_1 = 'Is your back pain associated with any of the following?'
    if question_number and request.args.get('answer') == 'Yes':
        header_1 = 'You need immediate care'
        explanation = """
            You answered 'Yes' to a question indicating you could be in need of emergency care. 
            Use the map below to see some providers
            """
        map_link = 'https://goo.gl/maps/zKXs4iFKqaqDwfJy6'
        return render_template('immediate_care.html', header_1=header_1, explanation=explanation, map_link=map_link)
    elif not question_number:
        question_number = 1
    elif question_number > num_question:
        return redirect(url_for('mobile_msk_questionaire'))
    question, answers, more_information = model.get_red_flag_question(question_number)
    return render_template('Red_Flags.html', header_1=header_1, question=question, answers=answers,
                           more_information=more_information, next_question_number=question_number+1)


@app.route('/Questionaire', methods=('GET', 'POST'))
def mobile_msk_questionaire():
    """
    The only real URL of the application. When the user calls it with a GET request it displays the questionnaire. Then
    when the user fills it out and sends back the answers to the questions via a post request, the answers are used to
    diagnose the user.
    """
    questions, answers = model.Get_Questions_And_Answers()  # Gets the questions and possible answers that will be used
    # To diagnose the patient.
    if request.method == 'POST':  # If the user has already filled out the questionnaire
        for q in questions:  # For each question q, each iteration q is a different question
            answers[q] = request.form.get(q)  # Get the answer to the question q
        diagnosis_URL = model.diagnose(questions, answers)  # Gets the diagnosis based on the answers to the questions
        return render_template('Diagnosis.html', questions=questions, answers=answers, diagnosis=diagnosis_URL)
    terms_conditions_url = url_for('temp_placeholder')  # Sets the URL for the terms and conditions
    return render_template('questionaire.html', questions=questions, answers=answers,
                           terms_conditions_url=terms_conditions_url)  # Display the questionnaire if
    # it has not been displayed yet


@app.route('/OSWENTRY_Back_Pain')
def OSWENTRY_Low_Back_Pain_Questionaire():
    """

    """
    questions = model.get_OSWENTRY_Questionnaire()
    post_URL = url_for('OSWENTRY_Low_Back_Pain_Questionaire_evaluation')
    return render_template('OSWENTRY_questionnaire.html', questions=questions, post_URL=post_URL)


@app.route('/OSWENTRY_Back_Pain', methods=['POST'])
def OSWENTRY_Low_Back_Pain_Questionaire_evaluation():
    """

    """
    score = model.score_OSWENTRY(request.form)
    disability = model.get_disability_level_from_score(score)
    return render_template('OSWENTRY_Results.html', score=score, disability=disability)

@app.route('/temp_placeholder', methods=('GET', 'POST'))
def temp_placeholder():
    return 'Temporary Placeholder'


if __name__ == '__main__':
    app.run()
# I wonder if we need to designate the run env. ex. (debug=True, host='0.0.0.0')???


class ExcelFile(object):
    def __init__(self, titles, column_names, data, tabnames, filename, single_sheet=False):
        if single_sheet:
            self.create_excel_file_single_sheet(titles, column_names, data, tabnames, filename)
        else:
            self.create_excel_file(titles, column_names, data, tabnames, filename)

    def create_excel_file(self, titles, column_names, data, tabnames, filename):
        my_excel = xl.Workbook(filename)
        length = len(tabnames)
        for i in range(length):
            my_worksheet = my_excel.add_worksheet()
            self.create_excel_sheet(my_worksheet, titles[i], column_names[i], tabnames[i], data[i])
        my_excel.close()

    def create_excel_file_single_sheet(self, titles, column_names, data, tabnames, filename):
        my_excel = xl.Workbook(filename)
        my_worksheet = my_excel.add_worksheet()
        self.create_excel_sheet(my_worksheet, titles, column_names, tabnames, data)
        my_excel.close()

    def create_excel_sheet(self, my_worksheet, title, column_names, tab_name, data):
        my_worksheet.name = tab_name

        row = 0
        col = 0
        for t in title:
            my_worksheet.write(row, col, t)
            col += 1
        col = 0
        row += 2

        for name in column_names:
            my_worksheet.write(row, col, name)
            col += 1

        col = 0
        row += 1

        for data_row in data:
            for data_cell in data_row:
                my_worksheet.write(row, col, data_cell)
                col += 1
            col = 0
            row += 1

def get_red_flag_question(question_number: int) -> Tuple[str, Tuple[str, str], str]:
    df = pd.read_csv('Moblie_MSK_Red_Flags.csv')
    row = list(df.iloc[question_number-1])
    question = row[0]
    answers = row[1:3]
    more_info = row[3]
    return question, answers, more_info

def Get_Questions_And_Answers():  # -> (list[str], dict[list[str]])
    """
    Returns a list of questions and a dictionary with the question as the key and a list of answers as the value
    """
    with open('QuestionProfiles.csv') as file:  # Opens the file with the questions and answers
        reader = csv.reader(file)  # Creates a reader object
        current = None  # Initialize
        answers = {}  # Initialize
        questions = []  # Initialize
        for row in reader:  # For Each Row in the file
            if row[0]:  # If the first column of the row has a value
                current = row[0]  # Set current to the value of the first column
                questions.append(current)  # append the first column/current question, to the list of questions
                answers[current] = []  # Initialize the list of answers to the current question
            answers[current].append(row[1])  # Add the answer to the question
    return questions, answers  # Return questions and answers

def diagnose(questions, answers):
    """
    Takes in questions and answers and the answers to the questions, then returns a link to the a google docs sheet with
    data on the given diagnosis.
    """
    links = {
        '1': 'https://docs.google.com/presentation/d/1cUBc5G1JMNM3qHb20wA3PAzc4kowVDpfTHVv_OD7nVk/edit?usp=sharing',
        '2': 'https://docs.google.com/presentation/d/1ZvTzRMkvk_bzaDNPCIq-XnxhGnb9ZjU_-tAo4yuKsZs/edit?usp=sharing',
        '3': 'https://docs.google.com/presentation/d/1r6Qr7hEGQztO4qXX8ogU0nRUVbbIv5dcyS0mZiAMGm0/edit?usp=sharing',
        '4': 'https://docs.google.com/presentation/d/1r6Qr7hEGQztO4qXX8ogU0nRUVbbIv5dcyS0mZiAMGm0/edit?usp=sharing'
    }  # Dictionary with links the the google docs for each of the given links
    # Note if the links to the google docs change, we need to edit the Links dictionary!!
    with open('QuestionProfiles.csv') as file:  # Open the question profile
        reader = csv.reader(file)
        num_classes = 0  # Initialize the number of classes
        for line in reader:  # Count the number of classes
            num_classes = max(len(line), num_classes)  # Num classes will be the row with the most columns
        num_classes -= 2  # Subtract 2 to make up for the first 2 columns
        file.seek(0)  # Return to the start of the file
        classes = [0 for _ in range(num_classes)]
        for row in reader:  # Diagnose the user using the answers they gave and the data in the CSV file
            if row[0]:  # If this row has a value in column 1, a question
                current = row[0]  # Set current to the question/value in column 1
            if row[1] == answers[current]:  # If this row has the answer the user chose
                for i in range(num_classes):  # For each profile/class
                    classes[i] += float(row[2+i])  # Add the value in the csv to each profiles total
    profile = str(classes.index(max(classes)) + 1)  # Find the diagnosis profile with the max value, then get the
    # number for it. This is the most likely diagnosis.
    return links[profile]  # Return the link to the document containing information on the diagnosis


def get_OSWENTRY_Questionnaire():
    with open('OSWESTRY_pain.csv') as file:  # Opens the file with the questions and answers
        reader = csv.reader(file)  # Creates a reader object
        questions = [row for i, row in enumerate(reader) if i]
    return questions


def score_OSWENTRY(answers):
    questions = get_OSWENTRY_Questionnaire()
    question_length = len(questions)
    score = 0
    for i in range(question_length):
        answer = answers.get(f'{i + 1}')
        if answer is None:
            continue
        score += (questions[i].index(answer) - 2)
    return score

def get_disability_level_from_score(score):
    if score < 5:
        return 'No Disability'
    elif score < 15:
        return 'Mild Disability'
    elif score < 25:
        return 'Moderate Disability'
    elif score < 35:
        return 'Severe Disability'
    else:
        return 'Completely Disabled'





# USER PROFILE CODE 

DATABASE = 'user_profiles.db'


def create_tables():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
                 full_name TEXT NOT NULL,
                 age INTEGER NOT NULL,
                 dob TEXT NOT NULL,
                 contact TEXT NOT NULL,
                 emergency_contact TEXT NOT NULL,
                 profile_photo TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS medical_records(id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 medical_problem TEXT NOT NULL,
                 FOREIGN KEY (user_id) REFERENCES users (id))''')

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        full_name = request.form['full_name']
        age = int(request.form['age'])
        dob = request.form['dob']
        contact = request.form['contact']
        emergency_contact = request.form['emergency_contact']
        profile_photo = request.files['profile_photo']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('''INSERT INTO users (full_name, age, dob, contact, emergency_contact, profile_photo)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (full_name, age, dob, contact, emergency_contact, profile_photo.filename))
        conn.commit()
        conn.close()

        profile_photo.save('static/profile_photos/' + profile_photo.filename)

        flash('Your profile has been created successfully!', 'success') 


        return redirect('/')

    return render_template('create_profile.html')


@app.route('/view_profile')
def view_profile():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    user = c.fetchone()
    conn.close()

    if user:
        return render_template('view_profile.html', user=user)
    else:
        return render_template('view_profile.html', message='Profile has not been created yet.')


@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if request.method == 'POST':
        full_name = request.form['full_name']
        age = int(request.form['age'])
        dob = request.form['dob']
        contact = request.form['contact']
        emergency_contact = request.form['emergency_contact']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('''UPDATE users SET full_name=?, age=?, dob=?, contact=?, emergency_contact=?
                     WHERE id=?''',
                  (full_name, age, dob, contact, emergency_contact, 1))  # Update the record with ID 1, adjust as needed

        conn.commit()
        conn.close()

        return redirect('/')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('SELECT * FROM users')
    user = c.fetchone()
    conn.close()

    if user:
        return render_template('update_profile.html', user=user)
    else:
        return render_template('update_profile.html', message='Profile has not been created yet.')


@app.route('/medical_records', methods=['GET', 'POST'])
def medical_records():
    if request.method == 'POST':
        medical_problem = request.form['medical_problem']

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute('''INSERT INTO medical_records (user_id, medical_problem)
                     VALUES (?, ?)''',
                  (1, medical_problem))  # Assign the record to user with ID 1, adjust as needed

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('medical_records.html')


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

