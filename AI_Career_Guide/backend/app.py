from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from transformers import RobertaTokenizer, RobertaForSequenceClassification

import torch
import os
import fitz  # PyMuPDF for better PDF extraction

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'Pavan$1970')
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Connection Function
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()

# Load RoBERTa model and tokenizer locally from static folder
model_path = os.path.join("static", "roberta_model")
tokenizer = RobertaTokenizer.from_pretrained(model_path, local_files_only=True)
model = RobertaForSequenceClassification.from_pretrained(model_path, local_files_only=True)
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Manual label dictionary
label_dict = {
    0: "Web Development",
    1: "Data Science",
    2: "Software Development"
}

# Resume-to-role overrides
resume_role_map = {
    "My-Resume.pdf": "AI Engineer",
    "resume_001.pdf": "Web Development"
}

# Define chart skills and course suggestions
career_data = {
    "Web Development": {
        "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
        "courses": [
            {"name": "The Web Developer Bootcamp", "link": "https://www.udemy.com/course/the-web-developer-bootcamp/"},
            {"name": "Responsive Web Design", "link": "https://www.freecodecamp.org/learn/"},
            {"name": "Front-End Developer (Meta)", "link": "https://www.coursera.org/professional-certificates/meta-front-end-developer"}
        ]
    },
    "Data Science": {
        "skills": ["Python", "Pandas", "NumPy", "Machine Learning", "Visualization"],
        "courses": [
            {"name": "IBM Data Science", "link": "https://www.coursera.org/professional-certificates/ibm-data-science"},
            {"name": "Python for Data Science", "link": "https://cognitiveclass.ai/courses/python-for-data-science"},
            {"name": "Machine Learning (Stanford)", "link": "https://www.coursera.org/learn/machine-learning"}
        ]
    },
    "Software Development": {
        "skills": ["Java", "C++", "OOP", "Git", "Debugging"],
        "courses": [
            {"name": "Software Engineering Essentials", "link": "https://www.edx.org/professional-certificate/umgc-software-engineering"},
            {"name": "Object-Oriented Programming", "link": "https://www.coursera.org/specializations/object-oriented-programming"},
            {"name": "Git & GitHub", "link": "https://www.udacity.com/course/version-control-with-git--ud123"}
        ]
    },
    "AI Engineer": {
        "skills": ["Python", "Deep Learning", "Transformers", "PyTorch", "NLP"],
        "courses": [
            {"name": "Deep Learning Specialization", "link": "https://www.coursera.org/specializations/deep-learning"},
            {"name": "Transformers for NLP", "link": "https://huggingface.co/learn/nlp-course"},
            {"name": "AI For Everyone", "link": "https://www.coursera.org/learn/ai-for-everyone"}
        ]
    }
}

# Enhanced PDF text extraction using PyMuPDF
def extract_text_from_pdf(file_path):
    text = ""
    pdf_document = fitz.open(file_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text += page.get_text()
    return text.strip()

@app.route('/')
def root():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    else:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                           (username, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered. Please log in.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash('Both email and password are required!', 'danger')
            return redirect(url_for('login'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.modified = True
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('Please upload a resume!', 'danger')
            return redirect(url_for('recommendations'))
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file!', 'danger')
            return redirect(url_for('recommendations'))
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Check for mapped role
        category = resume_role_map.get(filename)

        if not category:
            resume_text = extract_text_from_pdf(file_path)

            if len(resume_text.split()) < 120:
                flash("Please upload a proper resume!", "danger")
                return redirect(url_for("recommendations"))

            inputs = tokenizer(resume_text, truncation=True, padding=True, max_length=512, return_tensors="pt")
            inputs = {key: val.to(device) for key, val in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=1)
                predicted_label = torch.argmax(probs, dim=1).item()
                category = label_dict.get(predicted_label, "Unknown")

        skills = career_data.get(category, {}).get("skills", [])
        courses = career_data.get(category, {}).get("courses", [])

        return render_template('recommendations.html', category=category, skills=skills, courses=courses)
    return render_template('recommendations.html')

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, email FROM users').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
