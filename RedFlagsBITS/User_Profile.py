# User Profile 


from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
from flask import flash 

app = Flask(__name__)

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