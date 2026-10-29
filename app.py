from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

# SQLite database file path
DB_PATH = 'language_app.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # Allows dictionary-style access to columns (e.g., user['username'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Languages Table (Supports up to 20 languages)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Lessons Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id INTEGER,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (language_id) REFERENCES languages(id) ON DELETE CASCADE
        )
    ''')
    
    # Quiz Table (Supports 50 questions per language & explanations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_id INTEGER,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL,
            explanation TEXT NOT NULL,
            FOREIGN KEY (language_id) REFERENCES languages(id) ON DELETE CASCADE
        )
    ''')
    
    # Seed 20 Languages if empty
    cursor.execute("SELECT COUNT(*) FROM languages")
    if cursor.fetchone()[0] == 0:
        languages_list = [
            ("French", "fr"), ("Spanish", "es"), ("German", "de"), ("Italian", "it"),
            ("Portuguese", "pt"), ("Japanese", "ja"), ("Mandarin Chinese", "zh"), ("Korean", "ko"),
            ("Arabic", "ar"), ("Russian", "ru"), ("Hindi", "hi"), ("Dutch", "nl"),
            ("Turkish", "tr"), ("Polish", "pl"), ("Swedish", "sv"), ("Greek", "el"),
            ("Vietnamese", "vi"), ("Indonesian", "id"), ("Swahili", "sw"), ("Hebrew", "he")
        ]
        cursor.executemany("INSERT INTO languages (name, code) VALUES (?, ?)", languages_list)
        conn.commit()

    # Seed Sample Lessons and Questions if empty
    cursor.execute("SELECT COUNT(*) FROM lessons")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM languages WHERE code = 'fr'")
        fr_row = cursor.fetchone()
        fr_id = fr_row[0] if fr_row else 1

        cursor.execute("INSERT INTO lessons (language_id, title, content) VALUES (?, ?, ?)", 
                       (fr_id, "Lesson 1: Basic French Greetings", 
                        "1. Bonjour = Hello / Good Morning\n2. Merci = Thank you\n3. Au revoir = Goodbye\n4. Oui = Yes\n5. Non = No"))

    cursor.execute("SELECT COUNT(*) FROM quiz")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id FROM languages WHERE code = 'fr'")
        fr_row = cursor.fetchone()
        fr_id = fr_row[0] if fr_row else 1

        sample_questions = [
            (fr_id, "What is the English translation of 'Bonjour'?", "Goodbye", "Hello", "Thank You", "Please", "Hello", "'Bonjour' is the standard French greeting used during the day meaning 'Hello' or 'Good morning'."),
            (fr_id, "What does 'Merci' mean in English?", "Sorry", "Please", "Thank you", "Goodbye", "Thank you", "'Merci' translates directly to 'Thank you' in English."),
            (fr_id, "How do you say 'Goodbye' in French?", "Bonjour", "Au revoir", "Oui", "Non", "Au revoir", "'Au revoir' is the common parting phrase meaning 'Goodbye' until we meet again.")
        ]
        cursor.executemany("""
            INSERT INTO quiz (language_id, question, option_a, option_b, option_c, option_d, answer, explanation) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_questions)
        
    conn.commit()
    cursor.close()
    conn.close()

# Automatically initialize database tables and seed data on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        if not username or not password:
            flash('Please fill in all fields!', 'danger')
            return redirect(url_for('register'))
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Choose another.', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM languages")
    languages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', username=session['user'], languages=languages)

@app.route('/lesson/<int:lang_id>')
def lesson(lang_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM languages WHERE id = ?", (lang_id,))
    language = cursor.fetchone()
    
    cursor.execute("SELECT * FROM lessons WHERE language_id = ?", (lang_id,))
    lessons = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('lesson.html', language=language, lessons=lessons)

@app.route('/quiz/<int:lang_id>', methods=['GET', 'POST'])
def quiz(lang_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if 'quiz_lang_id' not in session or session['quiz_lang_id'] != lang_id or 'quiz_questions' not in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quiz WHERE language_id = ? LIMIT 50", (lang_id,))
        questions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not questions:
            flash('No questions available for this language yet.', 'warning')
            return redirect(url_for('dashboard'))
        
        session['quiz_lang_id'] = lang_id
        session['quiz_questions'] = [q['id'] for q in questions]
        session['current_index'] = 0
        session['score'] = 0
        session['answers_history'] = []

    questions_ids = session['quiz_questions']
    current_index = session['current_index']

    if current_index >= len(questions_ids):
        return redirect(url_for('quiz_result'))

    current_q_id = questions_ids[current_index]
    
    if request.method == 'POST':
        selected_option = request.form.get('option')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM quiz WHERE id = ?", (current_q_id,))
        current_q = cursor.fetchone()
        cursor.close()
        conn.close()
        
        is_correct = (selected_option == current_q['answer'])
        if is_correct:
            session['score'] += 1
            
        history = session.get('answers_history', [])
        history.append({
            'question': current_q['question'],
            'selected': selected_option,
            'correct': current_q['answer'],
            'is_correct': is_correct,
            'explanation': current_q['explanation']
        })
        session['answers_history'] = history
        session['current_index'] += 1
        
        if session['current_index'] >= len(questions_ids):
            return redirect(url_for('quiz_result'))
        
        return redirect(url_for('quiz', lang_id=lang_id))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quiz WHERE id = ?", (current_q_id,))
    quiz_data = cursor.fetchone()
    
    cursor.execute("SELECT * FROM languages WHERE id = ?", (lang_id,))
    language = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('quiz.html', quiz=quiz_data, language=language, current_num=current_index + 1, total_num=len(questions_ids))

@app.route('/quiz_result')
def quiz_result():
    if 'user' not in session or 'answers_history' not in session:
        return redirect(url_for('dashboard'))
    
    score = session.get('score', 0)
    total = len(session.get('quiz_questions', []))
    percentage = (score / total) * 100 if total > 0 else 0
    passed = percentage >= 70
    
    history = session.get('answers_history')
    
    session.pop('quiz_questions', None)
    session.pop('current_index', None)
    session.pop('score', None)
    session.pop('answers_history', None)
    session.pop('quiz_lang_id', None)
    
    return render_template('quiz_result.html', score=score, total=total, percentage=percentage, passed=passed, history=history)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)