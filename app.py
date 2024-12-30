import email
from tkinter.constants import CURRENT

from flask import Flask, render_template, request, redirect, session, url_for
import psycopg
from datetime import date

from pyexpat.errors import messages

app = Flask(__name__)

app.secret_key = 'super secret key'
database_connection_session = psycopg.connect(
    host="ep-square-dew-a59b9xyb.us-east-2.aws.neon.tech",
    dbname="neondb",
    user="neondb_owner",
    password="mO9lIUZN4bDW",
    port=5432
)

UPLOAD_FOLDER = 'static/uploads/'
today_date = date.today().strftime('%Y-%m-%d')  # used when choosing date for appointment
UPLOAD_SCANS = 'static/uploads/scans'


# saved the directory path in a global variable to use it anywhere
@app.route('/')  # This creates a function to connect '/' with home awl ma hayegy / hynady home (kol da fl url)
def home():
    user = session.get('user')  # or  userdata=session['user']
    patient_str = 'patient'
    radiologist_str = 'radiologist'
    message = request.args.get('message')

    if user:

        if user['role'] == 'Admin' or user['role'] == 'admin':
            cur2 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
            cur2.execute('select * from users')
            records1 = cur2.fetchall()
            cur2.execute(
                'SELECT * FROM allusers a INNER JOIN patients p ON a.email = p.email WHERE LOWER(a.role) = %s ',
                (patient_str,))
            records2 = cur2.fetchall()
            cur2.execute(
                'SELECT * FROM allusers a INNER JOIN radiologists r ON a.email = r.email WHERE LOWER(a.role) = %s',
                (radiologist_str,))
            records3 = cur2.fetchall()
            return render_template('index.html', user=user, usersdata=records1, patientsdata=records2,
                                   radiologistsdata=records3)

        elif user['role'] == 'patient' or user['role'] == 'Patient':
            email = user['email']
            cur2 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
            cur2.execute('SELECT * FROM patients WHERE email = %s ', (email,))
            records = cur2.fetchone()
            cur2.execute('SELECT * FROM radiologists')
            records2 = cur2.fetchall()
            cur2.execute('SELECT * FROM appointments WHERE patientid = %s', (records['patientid'],))
            records3 = cur2.fetchall()
            return render_template('p_profile.html', userdata=records, msg=message, today_date=today_date,
                                   radiologists=records2, appointments=records3)

        elif user['role'] == 'radiologist' or user['role'] == 'Radiologist':
            email = user['email']
            cur2 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
            cur2.execute('SELECT * FROM radiologists WHERE email = %s', (email,))
            records = cur2.fetchone()

            cur2.execute('SELECT * FROM appointments WHERE radiologistid = %s', (records['radiologistid'],))
            records3 = cur2.fetchall()

            cur2.execute('SELECT * FROM patient_scans ')
            records4 = cur2.fetchall()
            return render_template('radiologist.html', radiologist=records, msg=message, appointments=records3,scans=records4)




    else:
        return redirect('/main')


@app.route('/main')
def main():
    return render_template('main.html')


@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')


@app.route('/lmore')
def lmore():
    return render_template('lmore.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = request.args.get('msg')

    if request.method == 'GET':
        return render_template('register.html', msg=message)

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = 'patient'
        sex = request.form.get('sex')

        if password != confirm_password:
            message = 'Passwords do not match'
        else:
            # connect to database and store data
            cur = database_connection_session.cursor()
            cur.execute('SELECT * FROM allusers WHERE email = %s', (email,))
            if cur.fetchone():
                message = 'Email already registered'
            else:
                cur.execute('INSERT INTO patients(firstname, lastname, email,sex) values (%s,%s,%s,%s)',
                            (firstname, lastname, email, sex))  # written this way to make it less hackable
                cur.execute(
                    'INSERT INTO allusers(fname, lname, email, password,role) values (%s,%s,%s,%s,%s)',
                    (firstname, lastname, email, password, role))
                database_connection_session.commit()
                message = 'User registration successful'
                # without commit execution will only be saved temporarily to actually
                # save it in db we should commit

    return redirect(f'/register?msg={message}')


@app.route('/login', methods=['GET',
                              'POST'])  # This creates a function to connect '/' with home awl ma hayegy / hynady home (kol da fl url)
def login():
    message = request.args.get('msg')
    if request.method == 'GET':
        return render_template('login.html', msg=message)
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute('select * from allusers where email=%s and password=%s', (email, password))
        userdata = cur.fetchone()
        if userdata is None:
            # email or password is incorrect
            message = 'Email does not exist or password is incorrect'
            return redirect(f'/login?msg={message}')
        else:
            session['user'] = userdata
            return redirect('/')


@app.route('/logout')  # This creates a function to connect '/' with home awl ma hayegy / hynady home (kol da fl url)
def logout():
    session.pop('user', None)
    return redirect('/main')


@app.route('/delete/<int:id>/<int:role>')
def delete_user(id, role):
    # if role = 1 means admin , 2 means patient and 3 means radiologist
    cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    if role == 1:
        cur.execute('SELECT * FROM users WHERE id = %s', (id,))
        records = cur.fetchone()
        email = records['email']

        cur.execute('DELETE FROM allusers WHERE email=%s', (email,))
        cur.execute('DELETE FROM users WHERE id=%s', (id,))

        database_connection_session.commit()
    if role == 2:
        cur.execute('SELECT * FROM patients WHERE patientid = %s', (id,))
        records = cur.fetchone()
        email = records['email']

        cur.execute('DELETE FROM allusers WHERE email=%s', (email,))
        cur.execute('DELETE FROM patients WHERE patientid=%s', (id,))

        database_connection_session.commit()
    if role == 3:
        cur.execute('SELECT * FROM radiologists WHERE radiologistid = %s', (id,))
        records = cur.fetchone()
        email = records['email']

        cur.execute('DELETE FROM allusers WHERE email=%s', (email,))
        cur.execute('DELETE FROM radiologists WHERE radiologistid=%s', (id,))

        database_connection_session.commit()
    return redirect('/')


@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    message = request.args.get('msg')
    if request.method == 'GET':
        return render_template('AdminAddUser.html', msg=message)
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        sex = request.form.get('sex')
        role = request.form.get('role')
        salary = 0
        cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute('SELECT * FROM users where email=%s', (email,))
        records = cur.fetchone()
        if records is None:
            if role == 'admin' or role == 'Admin':
                cur.execute('INSERT INTO users(firstname, lastname, email,password) values (%s,%s,%s,%s)',
                            (firstname, lastname, email, password))  # written this way to make it less hackable
                cur.execute(
                    'INSERT INTO allusers(fname, lname, email, password,role) values (%s,%s,%s,%s,%s)',
                    (firstname, lastname, email, password, role))
                database_connection_session.commit()
                message = 'Admin added successfully'

            elif role == 'patient' or role == 'Patient':
                cur.execute('INSERT INTO patients(firstname, lastname, email,sex) values (%s,%s,%s,%s)',
                            (firstname, lastname, email, sex))  # written this way to make it less hackable
                cur.execute(
                    'INSERT INTO allusers(fname, lname, email, password,role) values (%s,%s,%s,%s,%s)',
                    (firstname, lastname, email, password, role))
                database_connection_session.commit()
                message = 'Patient registration successful'

            elif role == 'technician' or role == 'Technician':
                cur.execute('INSERT INTO technician(firstname, lastname, email,sex,salary) values (%s,%s,%s,%s,%s)',
                            (firstname, lastname, email, sex, salary))  # written this way to make it less hackable
                cur.execute(
                    'INSERT INTO allusers(fname, lname, email, password,role) values (%s,%s,%s,%s,%s)',
                    (firstname, lastname, email, password, role))
                database_connection_session.commit()
                message = 'Technician Added successfully'
            elif role == 'radiologist' or role == 'Radiologist':
                cur.execute('INSERT INTO radiologists(firstname, lastname, email,sex,salary) values (%s,%s,%s,%s,%s)',
                            (firstname, lastname, email, sex, salary))  # written this way to make it less hackable
                cur.execute(
                    'INSERT INTO allusers(fname, lname, email, password,role) values (%s,%s,%s,%s,%s)',
                    (firstname, lastname, email, password, role))
                database_connection_session.commit()
                message = 'Radiologist added successfully'

        else:
            message = 'User Already Exists'
            return redirect(f'/add-user?msg={message}')

    return redirect(f'/add-user?msg={message}')


@app.route('/edit/<int:id>/<int:role>', methods=['GET', 'POST'])
def edit_user(id, role):
    message = request.args.get('message')

    if request.method == 'GET':
        return render_template('EditAdmins.html', id=id, msg=message, role=role)

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        salary = request.form.get('salary')
        CURRENTemail = ''
        records = ''
        cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        if role == 1:
            cur.execute('SELECT * FROM users WHERE id = %s', (id,))
            records = cur.fetchone()

        elif role == 2:
            cur.execute('SELECT * FROM patients WHERE patientid = %s', (id,))
            records = cur.fetchone()

        elif role == 3:
            cur.execute('SELECT * FROM radiologists WHERE radiologistid = %s', (id,))
            records = cur.fetchone()
            if salary is None:
                salary = records['salary']

        CURRENTemail = records['email']

        if password != confirm_password:
            message = 'Passwords do not match'

        if CURRENTemail != email:
            # connect to database and store data
            cur2 = database_connection_session.cursor()
            cur2.execute('SELECT * FROM allusers WHERE email = %s', (email,))
            if cur2.fetchone():
                message = 'Email already Exists'

            else:
                cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)

                cur1.execute('UPDATE  allusers SET fname=%s , lname =%s , email=%s ,password=%s where email= %s ',
                             (firstname, lastname, email, password, CURRENTemail))  # written this way for security
                database_connection_session.commit()
                if role == 1:
                    cur.execute(
                        'UPDATE  users SET firstname=%s , lastname =%s , email=%s ,password=%s where email= %s ',
                        (firstname, lastname, email, password, CURRENTemail))
                    database_connection_session.commit()
                    message = 'Admin Edited Successfully'

                if role == 2:
                    cur.execute('UPDATE  patients SET firstname=%s , lastname =%s , email=%swhere email= %s ',
                                (firstname, lastname, email, CURRENTemail))
                    database_connection_session.commit()
                    message = 'Patient Edited Successfully'
                if role == 3:
                    cur.execute('UPDATE  radiologists SET firstname=%s , lastname =%s , email=%s where email= %s ',
                                (firstname, lastname, email, CURRENTemail))
                    database_connection_session.commit()
                    message = 'Radiologist Edited Successfully'
        if email == CURRENTemail:
            cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)

            cur1.execute('UPDATE  allusers SET fname=%s , lname =%s , email=%s ,password=%s where email= %s ',
                         (firstname, lastname, email, password, CURRENTemail))  # written this way for security
            database_connection_session.commit()
            cur.execute('UPDATE  users SET firstname=%s , lastname =%s , email=%s ,password=%s where email= %s ',
                        (firstname, lastname, email, password, CURRENTemail))
            database_connection_session.commit()
            message = 'Admin Edited Successfully'
            if role == 1:
                cur.execute('UPDATE  users SET firstname=%s , lastname =%s , email=%s ,password=%s where email= %s ',
                            (firstname, lastname, email, password, CURRENTemail))
                database_connection_session.commit()
                message = 'Admin Edited Successfully'

            if role == 2:
                cur.execute('UPDATE  patients SET firstname=%s , lastname =%s , email=%s  where email= %s ',
                            (firstname, lastname, email, CURRENTemail))
                database_connection_session.commit()
                message = 'Patient Edited Successfully'
            if role == 3:
                cur.execute(
                    'UPDATE  radiologists SET firstname=%s , lastname =%s , salary =%s ,email=%s  where email= %s ',
                    (firstname, lastname, salary, email, CURRENTemail))
                database_connection_session.commit()
                message = 'Radiologist Edited Successfully'

    return redirect(f'/edit/{id}/{role}?message={message}')


@app.route('/upload-profile-picture', methods=['GET', 'POST'])
def upload_profile_picture():
    user = session['user']
    if (user['role'] == 'patient' or user['role'] == 'Patient'):
        # getting patientid from patients table
        cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        cur1.execute("SELECT * FROM allusers a, patients p  WHERE (a.email=p.email)and(a.id=%s)",
                     (user['id'],))
        result = cur1.fetchone()
        patientid = result['patientid']

        message = request.form.get('message')

        file = request.files.get('editProfilePic')
        if not user:
            return redirect(url_for('login'))

        if not file:
            message = 'No file selected'
            return redirect('/?message={message}'.format(message=message))

        # Save the file
        filename = f"{patientid}_{file.filename}"
        filepath = UPLOAD_FOLDER + filename
        # created filepath but it's still empty

        with open(filepath, 'wb') as f:
            f.write(file.read())
            # reads the file from user and puts it in the filepath we created
        cur = database_connection_session.cursor()
        cur.execute("UPDATE patients SET profile_picture = %s WHERE patientid = %s",
                    (filepath, patientid))
        database_connection_session.commit()
        message = 'Profile Picture Uploaded Successfully'
        return redirect('/?message={message}'.format(message=message))
    else:
        cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        cur1.execute("SELECT * FROM allusers a, radiologists r  WHERE (a.email=r.email)and(a.id=%s)",
                     (user['id'],))
        result = cur1.fetchone()
        radiologistid = result['radiologistid']

        message = request.form.get('message')

        file = request.files.get('editProfilePic')
        if not user:
            return redirect(url_for('login'))

        if not file:
            message = 'No file selected'
            return redirect('/?message={message}'.format(message=message))

        # Save the file
        filename = f"{radiologistid}_{file.filename}"
        filepath = UPLOAD_FOLDER + filename
        # created filepath but it's still empty

        with open(filepath, 'wb') as f:
            f.write(file.read())
            # reads the file from user and puts it in the filepath we created
        cur = database_connection_session.cursor()
        cur.execute("UPDATE radiologists SET profile_picture = %s WHERE radiologistid = %s",
                    (filepath, radiologistid))
        database_connection_session.commit()
        message = 'Profile Picture Uploaded Successfully'
        return redirect('/?message={message}'.format(message=message))


@app.route('/edit_personal_info', methods=['GET', 'POST'])
def edit_personal_info():
    user = session['user']
    message = request.form.get('message')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    age = request.form.get('age')
    sex = request.form.get('gender')
    phonenumber = request.form.get('phonenumber')
    address = request.form.get('address')
    newpassword = request.form.get('newpassword')
    confirm_password = request.form.get('confirmpassword')

    if not user:
        return redirect(url_for('login'))
    else:
        cur = database_connection_session.cursor()
        if user['role'] == 'patient':
            cur.execute(
                'UPDATE  patients SET firstname=%s , lastname =%s ,age=%s,sex=%s,phonenumber=%s,address=%s  where email= %s ',
                (firstname, lastname, age, sex, phonenumber, address, user['email']))
            database_connection_session.commit()

        elif user['role'] == 'radiologist':
            cur.execute(
                'UPDATE  radiologists SET firstname=%s , lastname =%s,sex=%s,phonenumber=%s where email= %s ',
                (firstname, lastname, sex, phonenumber, user['email']))
            database_connection_session.commit()

    cur.execute('UPDATE  allusers SET fname=%s , lname =%s  where email= %s ', (firstname, lastname, user['email']))
    database_connection_session.commit()
    if ((newpassword == confirm_password) and newpassword is not None):
        cur.execute(
            'UPDATE  allusers SET password=%s  where email= %s ',
            (newpassword, user['email']))
        database_connection_session.commit()
    message = 'Personal info Edited Successfully'
    return redirect('/?message={message}'.format(message=message))


@app.route('/edit_medical_info', methods=['GET', 'POST'])
def edit_medical_info():
    user = session['user']
    message = request.form.get('message')
    allergies = request.form.get('allergies')
    cc = request.form.get('chronicConditions')
    pastT = request.form.get('pastTreatments')
    if not user:
        return redirect(url_for('login'))
    else:
        cur = database_connection_session.cursor()
        cur.execute('UPDATE  patients SET allergies=%s , cc=%s,pastt=%s WHERE email= %s',
                    (allergies, cc, pastT, user['email']))
        database_connection_session.commit()
        message = 'Medical Info Edited Successfully'
        return redirect('/?message={message}'.format(message=message))


@app.route('/schedule_appointment', methods=['GET', 'POST'])
def schedule_appointment():
    user = session['user']
    messages = request.form.get('messages')
    date = request.form.get('appointmentDate')
    time = request.form.get('appointmentTime')
    radiologistid = request.form.get('doctorName')

    cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    cur1.execute("SELECT * FROM allusers a, patients p  WHERE (a.email=p.email)and(a.id=%s)",
                 (user['id'],))
    result = cur1.fetchone()

    patientid = result['patientid']
    patientname = result['firstname']

    cur1.execute("SELECT * FROM radiologists where radiologistid=%s  ", (radiologistid,))
    result2 = cur1.fetchone()
    radiologistname = result2['firstname']
    if not user:
        return redirect(url_for('login'))
    else:
        cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute('SELECT * FROM appointments   WHERE appointmentdate=%s and timeslot=%s and radiologistid=%s',
                    (date, time, radiologistid))
        result = cur.fetchone()
        if result:
            message = 'Sorry patient is already scheduled try finding another appointment'
            return redirect('/?message={message}'.format(message=message))
        else:
            cur.execute(
                'INSERT INTO appointments (appointmentdate, timeslot, radiologistid, radiologistname, patientname, patientid) VALUES (%s, %s, %s, %s, %s, %s)',
                (date, time, radiologistid, radiologistname, patientname, patientid))
            database_connection_session.commit()
            message = 'Appointment Scheduled Successfully'

        return redirect('/?message={message}'.format(message=message))


@app.route('/cancel_app/<int:id>', methods=['GET', 'POST'])
def cancel_app(id):
    # id stands for appointmentid
    messages = request.args.get('messages')
    cur = database_connection_session.cursor()
    cur.execute('DELETE FROM appointments WHERE appointmentid=%s ', (id,))
    database_connection_session.commit()
    message = 'Appointment Canceled Successfully'
    return redirect('/?message={message}'.format(message=message))


@app.route('/upload_scans', methods=['POST'])
def upload_scans():
    user = session['user']

    # getting patientid to save the file with a name representing each patient
    cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    cur1.execute("SELECT * FROM allusers a, patients p  WHERE (a.email=p.email)and(a.id=%s)",
                 (user['id'],))
    result = cur1.fetchone()
    patientid = result['patientid']
    if not user:
        return redirect(url_for('login'))
    file = request.files.get('medical_files')
    if not file:
        message = 'No file selected for upload'
        return redirect('/?message={message}'.format(message=message))
    # Save the file
    filename = f"{patientid}_{file.filename}"
    filepath = UPLOAD_SCANS + filename
    cur = database_connection_session.cursor()
    cur.execute('SELECT * FROM patient_scans where patientid=%s and scans=%s', (patientid, filepath))
    result = cur.fetchone()
    if result:
        message = 'Patient already exists'
        return redirect('/?message={message}'.format(message=message))
    else:
        with open(filepath, 'wb') as f:
            f.write(file.read())
            print(f"File saved to: {filepath}")
            # reads the file from user and puts it in the filepath we created
        cur1 = database_connection_session.cursor()
        cur1.execute("INSERT INTO patient_scans (scans, patientid) VALUES (%s, %s)",
                     (filepath, patientid))
        database_connection_session.commit()
        message = 'File Uploaded Successfully'
        return redirect('/?message={message}'.format(message=message))


@app.route('/submit_inquiry', methods=['POST'])
def submit_inquiry():
    user = session['user']
    messages = request.form.get('messages')
    inquiry = request.form.get('inquiry')
    request_message = request.form.get('request')

    # getting patientid to save in the database table each req & inq corresponding to each patientid
    cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    cur1.execute("SELECT * FROM allusers a, patients p  WHERE (a.email=p.email)and(a.id=%s)",
                 (user['id'],))
    result = cur1.fetchone()
    patientid = result['patientid']

    if inquiry and request_message:
        # Insert both the inquiry and request into your database
        cur = database_connection_session.cursor()
        cur.execute("INSERT INTO requests_inquiries (inquiry, request,patientid) VALUES (%s, %s,%s)",
                    (inquiry, request_message, patientid))
        database_connection_session.commit()
        message = "Your inquiry and request have been submitted successfully."
    else:
        message = "Please fill in both fields."

    return redirect('/?message={message}'.format(message=message))


@app.route('/admin-analytics')
def admin_analytics():
    cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)

    # Example analytics data
    cur.execute("SELECT COUNT(*) as user_count FROM allusers")
    user_count = cur.fetchone()

    cur.execute("SELECT COUNT(*) as patient_count FROM patients")
    patient_count = cur.fetchone()

    cur.execute("SELECT COUNT(*) as radiologist_count FROM radiologists")
    radiologist_count = cur.fetchone()

    # Total salary and average salary of radiologists
    cur.execute("SELECT SUM(salary) as total_salary, AVG(salary) as avg_salary FROM radiologists")
    salary_data = cur.fetchone()

    # Count number of admins
    cur.execute("SELECT COUNT(*) as admin_count FROM allusers WHERE role = 'admin' or role = 'Admin'")
    admin_count = cur.fetchone()

    # Round avg_salary to two decimal places
    avg_salary = round(salary_data['avg_salary'], 2)

    return render_template('admin_analytics.html',
                           user_count=user_count['user_count'],
                           patient_count=patient_count['patient_count'],
                           radiologist_count=radiologist_count['radiologist_count'],
                           total_salary=salary_data['total_salary'],
                           avg_salary=avg_salary,
                           admin_count=admin_count['admin_count'])


@app.route('/admin-p-inquiry', methods=['GET', 'POST'])
def admin_p_inquiry():
    user = session['user']
    messages = request.form.get('messages')
    if user is None:
        return redirect('/main')
    cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    cur.execute("SELECT * FROM requests_inquiries")
    records = cur.fetchall()
    return render_template('admin_p_inquiry.html', inquiries=records)


@app.route('//admin-appointment', methods=['GET', 'POST'])
def admin_appointment():
    user = session['user']
    if user is None:
        return redirect('/main')
    cur = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    cur.execute("SELECT * FROM appointments")
    records = cur.fetchall()
    return render_template('admin_appointment.html', appointments=records)


@app.route('/action/<int:id>/<int:action>', methods=['GET', 'POST'])
def action(id, action):
    user = session['user']
    cur = database_connection_session.cursor()
    cur1 = database_connection_session.cursor(row_factory=psycopg.rows.dict_row)
    confirm_str = 'confirm'
    postponed_str = 'postpone '
    if user is None:
        return redirect('/main')
    else:
        if action == 1:
            cur.execute('UPDATE appointments SET status=%s WHERE appointmentid=%s', (confirm_str, id))
            database_connection_session.commit()
        elif action == 2:
            cur.execute('UPDATE appointments SET status=%s WHERE appointmentid=%s', (postponed_str, id))
            database_connection_session.commit()
        elif action == 3:
            cur.execute('DELETE FROM appointments WHERE appointmentid=%s', (id,))
            database_connection_session.commit()
    if user['role'] == 'admin':
        return redirect('/admin-appointment')
    else:
        return redirect('/')


    if __name__ == '__main__':  #allows me to debug
        app.run(debug=True)
