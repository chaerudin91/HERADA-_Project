from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.database import get_db
from flask_mysqldb import MySQL
from tensorflow.keras.models import load_model
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db   
import numpy as np
from mysql.connector import Error, IntegrityError
import google.generativeai as genai
import langdetect
from google.cloud import dialogflow_v2 as dialogflow
from sklearn.linear_model import LogisticRegression

main = Blueprint('main', __name__)

# Load the model once when the app starts
model = load_model('models/Improved_Keras_model.h5')

@main.route('/prediksi')
def prediksi():
    return render_template('HOME/prediksi.html')

@main.route('/berita')
def berita():
    return render_template('berita.html')

@main.route('/komunitas')
def komunitas():
    return render_template('komunitas.html')

@main.route('/predict', methods=['POST'])
def predict():
    try:
        # Parse the JSON data from the request
        data = request.get_json()

        # Check if all required fields are present
        required_fields = [
            'snoring_rate', 'respiration_rate', 'body_temperature', 
            'limb_movement', 'blood_oxygen', 'eye_movement', 
            'sleeping_hours', 'heart_rate'
        ]
        
        # Validate that all fields are present
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        # Extract features from the data
        snoring_rate = data['snoring_rate']
        respiration_rate = data['respiration_rate']
        body_temperature = data['body_temperature']
        limb_movement = data['limb_movement']
        blood_oxygen = data['blood_oxygen']
        eye_movement = data['eye_movement']
        sleeping_hours = data['sleeping_hours']
        heart_rate = data['heart_rate']

        # Create feature array for prediction
        # Make sure the input is a 2D array with one row and eight features
        features = np.array([[snoring_rate, respiration_rate, body_temperature, limb_movement,
                              blood_oxygen, eye_movement, sleeping_hours, heart_rate]])

        # Make prediction using the model
        prediction = model.predict(features)

        # Assuming the model returns a value between 0 and 1 indicating stress level
        # Map prediction to the corresponding stress level
        stress_level = int(prediction[0][0] * 4) + 1  # Convert to a range from 1 to 4
        
        # Return the result as a JSON response
        return jsonify({'stress_level': stress_level})

    except Exception as e:
        # Return error response in case of failure
        return jsonify({'error': f'Error in prediction: {str(e)}'}), 500
    

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Mengecek username dan password dari database
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):  # Memeriksa password terenkripsi
                # Set session jika login berhasil
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('main.home'))  # Mengarahkan ke halaman home setelah login
            else:
                flash('Username atau password salah!', 'danger')
        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
    
    return render_template('login.html')

# Route untuk halaman Home (halaman setelah login)
@main.route('/home')
def home():
    # Pastikan hanya pengguna yang login yang bisa mengakses halaman ini
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    return render_template('HOME/home.html')

# Route untuk registrasi
@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validasi password dan confirm_password
        if password != confirm_password:
            flash("Password dan Konfirmasi Password tidak cocok!", "danger")
            return redirect(url_for('main.register'))
        
        # Hash password sebelum disimpan ke database
        hashed_password = generate_password_hash(password)
        
        # Simpan pengguna baru ke database
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            db.commit()
            flash("Akun berhasil dibuat!", "success")
            return redirect(url_for('main.login'))  # Arahkan ke halaman login setelah sukses
        except Exception as e:
            flash(f"Terjadi kesalahan: {str(e)}", "danger")
            return redirect(url_for('main.register'))
    
    return render_template('register.html')

# Konfigurasi API Key untuk Google Generative AI
my_api_key_gemini = 'AIzaSyAjj1UeMHPVxHhCvxaehmw6IcoleelNe9E'  # Ganti dengan API key Anda
genai.configure(api_key=my_api_key_gemini)

# Route untuk halaman utama
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/konsultasi', methods=['GET', 'POST'])
def konsultasi():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Menjalankan query untuk membaca data dari tabel psicologist
    cursor.execute("SELECT * FROM psychologists")
    psychologists = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('HOME/konsultasi.html', psychologists=psychologists)

# Route untuk konsultasi dengan psikolog berdasarkan ID
@main.route('/consult/<int:psychologist_id>')
def consult(psychologist_id):
    try:
        # Membuka koneksi ke database dan mengambil data psikolog berdasarkan ID
        cur = get_db().cursor(dictionary=True)  # Gunakan get_db untuk mendapatkan koneksi
        cur.execute("SELECT * FROM psychologists WHERE id = %s", (psychologist_id,))  # Menggunakan parameterisasi
        psychologist = cur.fetchone()  # Ambil data psikolog berdasarkan ID
        cur.close()  # Pastikan cursor ditutup

        # Jika psikolog ditemukan, tampilkan halaman konsultasi
        if psychologist:
            return render_template('HOME/consultation.html', psychologist=psychologist)
        else:
            # Jika psikolog tidak ditemukan, beri tahu pengguna
            flash('Psikolog tidak ditemukan.', 'danger')
            return redirect(url_for('main.konsultasi'))

    except Exception as e:
        # Jika terjadi error, beri tahu pengguna dan arahkan ke halaman error
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('main.home'))


def categorize_wellbeing(score, max_score):
    percentage = (score / max_score) * 100  # Menghitung persentase
    if percentage <= 20:
        return "Sangat Tinggi"
    elif percentage <= 40:
        return "Tinggi"
    elif percentage <= 60:
        return "Cukup Tinggi"
    elif percentage <= 80:
        return "Rendah"
    else:
        return "Sangat Rendah"


# Route untuk survei
@main.route('/survey', methods=['GET', 'POST'])
def survey():
    questions = [
        "Saya merasa cemas atau gelisah.",
        "Saya merasa tidak berdaya.",
        "Saya kesulitan tidur di malam hari.",
        "Saya merasa tidak bersemangat.",
        "Saya merasa mudah tersinggung.",
        "Saya merasa tertekan.",
        "Saya merasa tidak ada harapan.",
        "Saya merasa sulit berkonsentrasi.",
        "Saya merasa kesepian.",
        "Saya merasa tidak nyaman di sekitar orang lain.",
        "Saya merasa tidak memiliki teman.",
        "Saya sering merasa cemas.",
        "Saya merasa tidak bisa mengatasi stres.",
        "Saya merasa kualitas hidup saya rendah.",
        "Saya merasa tidak bahagia.",
        "Saya sering merasa marah.",
        "Saya merasa tidak puas dengan hidup saya.",
        "Saya merasa sulit mengambil keputusan.",
        "Saya merasa hidup saya tidak memiliki tujuan.",
        "Saya merasa cemas tentang masa depan.",
        "Saya merasa lelah sepanjang waktu.",
        "Saya sering merasa putus asa.",
        "Saya merasa bersalah tentang hal-hal yang telah saya lakukan.",
        "Saya merasa khawatir tentang kesehatan saya.",
        "Saya merasa mudah tersakiti.",
        "Saya merasa tidak ada orang yang peduli pada saya.",
        "Saya merasa terasing.",
        "Saya merasa tidak memiliki kontrol atas hidup saya.",
        "Saya merasa tertekan dengan pekerjaan saya.",
        "Saya merasa takut untuk mencoba hal-hal baru.",
        "Saya merasa tidak ada yang ingin mendengarkan saya.",
        "Saya merasa stres karena tuntutan hidup."
    ]

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        
        if not name or not age:
            flash("Nama dan umur harus diisi!", "danger")
            return redirect(url_for('survey'))

        total_score = 0
        max_score = len(questions) * 5  # Misalnya, nilai maksimal setiap pertanyaan adalah 4

        for i in range(len(questions)):
            score = int(request.form[f'question_{i}'])
            total_score += score

        wellbeing_category = categorize_wellbeing(total_score, max_score)

        # Simpan data ke database
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO wellbeing_responses (name, age, score, wellbeing_category) VALUES (%s, %s, %s, %s)",
                (name, age, total_score, wellbeing_category)
            )
            db.commit()
            flash("Terima kasih telah mengisi survei. Hasil Anda telah disimpan!", "success")
        except Exception as e:
            flash(f"Terjadi kesalahan saat menyimpan data: {str(e)}", "danger")

        return redirect(url_for('main.result', name=name, age=age, score=total_score, category=wellbeing_category))

    return render_template('HOME/survey.html', questions=questions)

@main.route('/result')
def result():
    name = request.args.get('name')
    age = request.args.get('age')
    score = request.args.get('score')
    category = request.args.get('category')

    return render_template('HOME/result.html', name=name, age=age, score=score, category=category)

# Fungsi untuk integrasi dengan Dialogflow
def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    return response.query_result.fulfillment_text

# Fungsi untuk menghasilkan respons menggunakan Generative AI
def generate_response(prompt, language):
    if language == 'id':
        prompt = f"Sebagai psikolog, berikan respons empatik dalam bahasa Indonesia dengan bahasa manusia untuk: {prompt}"
    else:
        prompt = f"As a psychologist, provide empathetic responses in Indonesian with human language to:: {prompt}"
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text if response.text else "Maaf, saya tidak bisa merespons saat ini. Silakan coba lagi nanti."
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"

# Route untuk chatbot
@main.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'messages' not in session:
        session['messages'] = []  # Inisialisasi list percakapan

    if request.method == 'POST':
        user_message = request.form.get('user_message')
        if user_message:
            # Simpan pesan pengguna
            session['messages'].append({'sender': 'user', 'text': user_message})

            # Deteksi bahasa
            language = langdetect.detect(user_message)

            # Hasilkan respons menggunakan Generative AI
            bot_response = generate_response(user_message, language)

            # Simpan respons chatbot
            session['messages'].append({'sender': 'bot', 'text': bot_response})

            # Simpan perubahan ke session
            session.modified = True

    # Ambil semua pesan untuk ditampilkan di template
    messages = session['messages']
    return render_template('HOME/chat.html', messages=messages)

@main.route('/clear_chat', methods=['POST'])
def clear_chat():
    session.pop('messages', None)  # Hapus semua pesan dari session
    return redirect(url_for('main.chat'))  

@main.route('/logout')
def logout():
    # Logic untuk logout pengguna, misalnya menghapus sesi atau token autentikasi
    session.clear()  # Menghapus sesi
    return redirect(url_for('main.login')) 