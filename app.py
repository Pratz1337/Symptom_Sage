from flask import Flask, render_template, redirect, url_for, request, session,send_from_directory
import mysql.connector
import os
from werkzeug.utils import secure_filename
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
from PIL import Image
import io
import tensorflow as tf
from tensorflow.keras.models import load_model
import cv2
import numpy as np
app = Flask(__name__)
app.secret_key = 'your_secret_key'


UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="pratz1337",
        database="symptomsage"
    )
    return db


with app.app_context():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS doctors
                 (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), age INT, gender VARCHAR(10), password VARCHAR(255), hospital VARCHAR(255))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS patients
                 (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), age INT, gender VARCHAR(10), password VARCHAR(255), scan_path VARCHAR(255), result VARCHAR(255), detailed_rep TEXT, prescription TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS doctor_patient_map
                 (id INT AUTO_INCREMENT PRIMARY KEY, doctor_id INT, patient_id INT)''')
    db.commit()
    cursor.close()
    db.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/auth')
def auth():
    return render_template('auth.html')
@app.route('/documentation')
def documentation():
    return render_template('documentation.html')
class PneumoniaDetector:
    def __init__(self, model_path, image_path):
        self.model_path = model_path
        self.image_path = image_path
        self.loaded_model = tf.keras.models.load_model(self.model_path)

    def predict(self):
        img = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
        resized_img = cv2.resize(img, (150, 150))
        img_array = np.array(resized_img) / 255
        img_array = img_array.reshape(1, 150, 150, 1)

        predictions = self.loaded_model.predict(img_array)
        if predictions[0] > 0.5:
            return "PNEUMONIA"
        else:
            return "NORMAL"

def generate(image_path):
    vertexai.init(project="airy-gate-418807", location="asia-southeast1")
    
    with open(image_path, "rb") as f:
        image = Image.open(f)
        image_data = io.BytesIO()
        image.save(image_data, format="PNG")
        image_data = image_data.getvalue()

    model = GenerativeModel("gemini-1.0-pro-vision-001")
    
    image_part = Part.from_data(
        mime_type="image/png",
        data=image_data,
    )

    text_input = """WRITE 'THIS IS A DETAILED REPORT OF THE SCAN (MAY OR MAYNOT BE ACCURATE)' WRITE A VERY DETAILED REPORT OF THE X-RAY REPORT OF THE SCAN in english. GIVE THE OUTPUT IN THIS FORMAT : {'FINDINGS:'}
    explain in complete medical terms should contain 500 words explaining the compllete medical problem. NOTE--> if the provided image is not an X-Ray GIVE OUTPUT- NOT AN XRAY"""

    generation_config = {
        "temperature": 0.1218484,
        "top_p": 0.5,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    responses = model.generate_content(
        [image_part, text_input],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    result = ""
    for response in responses:
        result += response.text

    return result
@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name FROM doctors WHERE name = %s AND password = %s", (name, password))
        doctor = cursor.fetchone()
        cursor.close()
        db.close()
        if doctor:
            session['doctor_id'] = doctor[0]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT patient_id FROM doctor_patient_map WHERE doctor_id = %s", (doctor[0],))
            patient_ids = [p[0] for p in cursor.fetchall()]
            if patient_ids:
                placeholders = ','.join(['%s'] * len(patient_ids))
                cursor.execute(f"SELECT name FROM patients WHERE id IN ({placeholders})", tuple(patient_ids))
                patient_names = [p[0] for p in cursor.fetchall()]
                session['patient_names'] = ', '.join(patient_names)
            else:
                session['patient_names'] = ''
            cursor.close()
            db.close()
            return redirect(url_for('doctor_dashboard'))
        else:
            return render_template('doctor_login.html', error='Invalid credentials')
    return render_template('doctor_login.html')

@app.route('/doctor_signup', methods=['GET', 'POST'])
def doctor_signup():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        password = request.form['password']
        hospital = request.form['Hospital']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO doctors (name, age, gender, password, hospital) VALUES (%s, %s, %s, %s, %s)", (name, age, gender, password, hospital))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('doctor_login'))
    return render_template('doctor_signup.html')

@app.route('/doctor_dashboard')
def doctor_dashboard():
    doctor_id = session['doctor_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.name, p.age, p.gender, p.scan_path, p.result, p.detailed_rep, p.prescription
        FROM patients p
        INNER JOIN doctor_patient_map dpm ON p.id = dpm.patient_id
        WHERE dpm.doctor_id = %s
        ORDER BY p.id DESC
    """, (doctor_id,))
    patients = cursor.fetchall()
    
    patient_reports = {}
    for patient in patients:
        name = patient[0]
        if name not in patient_reports:
            patient_reports[name] = []
        patient_reports[name].append(patient)
    
    cursor.close()
    db.close()
    return render_template('doctor_dashboard.html', patient_reports=patient_reports)

@app.route('/patient_login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM patients WHERE name = %s AND password = %s", (name, password))
        patient = cursor.fetchone()
        cursor.close()
        db.close()
        if patient:
            session['patient_id'] = patient[0]
            return redirect(url_for('patient_dashboard'))
        else:
            return render_template('patient_login.html', error='Invalid credentials')
    return render_template('patient_login.html')

@app.route('/patient_signup', methods=['GET', 'POST'])
def patient_signup():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO patients (name, age, gender, password) VALUES (%s, %s, %s, %s)", (name, age, gender, password))
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('patient_login'))
    return render_template('patient_signup.html')

@app.route('/patient_dashboard')
def patient_dashboard():
    patient_id = session.get('patient_id')
    
    if patient_id is None:
        return "Patient ID not found in session"
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT p.name, p.age, p.gender, p.scan_path, p.result, p.detailed_rep, p.prescription, d.name AS doctor_name, d.hospital
            FROM patients p
            LEFT JOIN doctor_patient_map dpm ON p.id = dpm.patient_id
            LEFT JOIN doctors d ON dpm.doctor_id = d.id
            WHERE p.id = %s
        """, (patient_id,))
        patient = cursor.fetchone()
        
        if patient is None:
            return "Patient not found in the database"
        
        return render_template('patient_dashboard.html', patient=patient)
    
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
    finally:
        cursor.close()
        db.close()
@app.route('/health_tracker', methods=['GET', 'POST'])
def health_tracker():
    patient_id = session['patient_id']
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medication_tracking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT,
            medicine VARCHAR(255),
            taken VARCHAR(10),
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')
    db.commit()

    cursor.execute("SELECT scan_path, prescription FROM patients WHERE id = %s", (patient_id,))
    patient_data = cursor.fetchall()

    message = None  # Initialize message variable

    if request.method == 'POST':
        all_medicines_taken = True  # Flag to track if all medicines are taken
        for data in patient_data:
            
            prescription = data[1]
            medicines = prescription.split(', ')
            for medicine in medicines:
                taken = request.form.get(medicine, 'off')
                if taken == 'off':
                    all_medicines_taken = False
                    break
            if not all_medicines_taken:
                break

        if all_medicines_taken:
            message = "All medicines taken for today"
        else:
            message = "Some medicines are not taken"

        # Store the medication tracking data in the database
        for data in patient_data:
            prescription = data[1]
            medicines = prescription.split(', ')
            for medicine in medicines:
                taken = request.form.get(medicine, 'off')
                cursor.execute("INSERT INTO medication_tracking (patient_id, medicine, taken) VALUES (%s, %s, %s)",
                               (patient_id, medicine, taken))
        db.commit()

    cursor.close()
    db.close()
    return render_template('health_tracker.html', patient_data=patient_data, message=message)


@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        result = request.form['result']
        detailed_rep = request.form['detailed_rep']
        num_medicines = int(request.form['num_medicines'])
        prescription = []
        for i in range(num_medicines):
            medicine = request.form[f'medicine_{i}']
            prescription.append(medicine)
        prescription = ', '.join(prescription)
        doctor_id = session['doctor_id']
        db = get_db()
        cursor = db.cursor()

        file = request.files['scan_path']
        scan_path = None  # Initialize scan_path as None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            scan_path = filename  # Store the filename in the database

        cursor.execute("SELECT id FROM patients WHERE name = %s", (name,))
        patient = cursor.fetchone()

        if patient:
            patient_id = patient[0]
            cursor.execute("UPDATE patients SET age=%s, gender=%s, scan_path=%s, result=%s, detailed_rep=%s, prescription=%s WHERE id=%s",
                           (age, gender, scan_path, result, detailed_rep, prescription, patient_id))
        else:
            cursor.execute("INSERT INTO patients (name, age, gender, scan_path, result, detailed_rep, prescription) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (name, age, gender, scan_path, result, detailed_rep, prescription))
            patient_id = cursor.lastrowid

        cursor.execute("SELECT id FROM doctor_patient_map WHERE doctor_id = %s AND patient_id = %s", (doctor_id, patient_id))
        mapping = cursor.fetchone()

        if not mapping:
            cursor.execute("INSERT INTO doctor_patient_map (doctor_id, patient_id) VALUES (%s, %s)", (doctor_id, patient_id))

        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('doctor_dashboard'))

    return render_template('add_patient.html')
@app.route('/remove_patient', methods=['GET', 'POST'])
def remove_patient():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        doctor_id = session['doctor_id']
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM patients WHERE name = %s", (patient_name,))
        result = cursor.fetchone()

        if result:
            patient_id = result[0]

            cursor.execute("DELETE FROM doctor_patient_map WHERE doctor_id = %s AND patient_id = %s", (doctor_id, patient_id))
            db.commit()

        cursor.close()
        db.close()
        return redirect(url_for('doctor_dashboard'))

    return render_template('remove_patient.html')
@app.route('/analyse', methods=['GET', 'POST'])
def analyse():
    if request.method == 'POST':
        image_file = request.files['image_file']
        image_filename = image_file.filename
        image_path = os.path.join('uploads', image_filename)
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        model_path = r'C:\Users\sayal\OneDrive\Desktop\SymptomSage\src\Pneumonia_model.keras'
        detector = PneumoniaDetector(model_path, os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        prediction = detector.predict()

        generated_report = generate(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        generated_report=generated_report.replace('**','')
        report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{image_filename.split('.')[0]}_report.txt")
        with open(report_path, "w") as f:
            f.write(generated_report)

        patient_name = "John Doe"
        scan_dates = ["2023-04-01", "2023-06-15", "2023-09-20", "2024-01-10", "2024-03-28"]
        

        return render_template('analyse.html', prediction=prediction, generated_report=generated_report, image_path=image_path, patient_name=patient_name, scan_dates=scan_dates)

    return render_template('analyse.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
if __name__ == '__main__':
    app.run(debug=True)