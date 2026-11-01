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
    
    # Quiz Table (Supports multiple questions per language & explanations)
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

    # Seed Native Lessons for ALL 20 languages if lessons table is empty
    cursor.execute("SELECT COUNT(*) FROM lessons")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, code, name FROM languages")
        all_langs = cursor.fetchall()
        
        vocab_samples = {
            'fr': (
                "Lesson 1: French Essentials & Everyday Communication",
                "1. Greetings:\n   - Bonjour = Hello / Good Morning\n   - Salut = Hi / Bye (Informal)\n   - Bonsoir = Good Evening\n\n"
                "2. Courtesies:\n   - Merci = Thank you\n   - S'il vous plaît = Please\n   - De rien = You're welcome\n\n"
                "3. Farewells:\n   - Au revoir = Goodbye\n   - À bientôt = See you soon\n\n"
                "4. Basic Responses:\n   - Oui = Yes\n   - Non = No"
            ),
            'es': (
                "Lesson 1: Spanish Essentials & Everyday Communication",
                "1. Greetings:\n   - Hola = Hello / Hi\n   - Buenos días = Good morning\n   - Buenas tardes = Good afternoon\n\n"
                "2. Courtesies:\n   - Gracias = Thank you\n   - Por favor = Please\n   - De nada = You're welcome\n\n"
                "3. Farewells:\n   - Adiós = Goodbye\n   - Hasta luego = See you later\n\n"
                "4. Basic Responses:\n   - Sí = Yes\n   - No = No"
            ),
            'de': (
                "Lesson 1: German Essentials & Everyday Communication",
                "1. Greetings:\n   - Hallo = Hello\n   - Guten Morgen = Good morning\n   - Guten Tag = Good day\n\n"
                "2. Courtesies:\n   - Danke = Thank you\n   - Bitte = Please / You're welcome\n   - Entschuldigung = Excuse me\n\n"
                "3. Farewells:\n   - Auf Wiedersehen = Goodbye\n   - Tschüss = Bye\n\n"
                "4. Basic Responses:\n   - Ja = Yes\n   - Nein = No"
            ),
            'it': (
                "Lesson 1: Italian Essentials & Everyday Communication",
                "1. Greetings:\n   - Ciao = Hello / Hi\n   - Buongiorno = Good morning\n   - Buonasera = Good evening\n\n"
                "2. Courtesies:\n   - Grazie = Thank you\n   - Per favore = Please\n   - Prego = You're welcome\n\n"
                "3. Farewells:\n   - Arrivederci = Goodbye\n   - Ciao = Bye\n\n"
                "4. Basic Responses:\n   - Sì = Yes\n   - No = No"
            ),
            'pt': (
                "Lesson 1: Portuguese Essentials & Everyday Communication",
                "1. Greetings:\n   - Olá = Hello\n   - Bom dia = Good morning\n   - Boa tarde = Good afternoon\n\n"
                "2. Courtesies:\n   - Obrigado / Obrigada = Thank you\n   - Por favor = Please\n   - De nada = You're welcome\n\n"
                "3. Farewells:\n   - Adeus = Goodbye\n   - Até logo = See you later\n\n"
                "4. Basic Responses:\n   - Sim = Yes\n   - Não = No"
            ),
            'ja': (
                "Lesson 1: Japanese Essentials & Everyday Communication",
                "1. Greetings:\n   - Konnichiwa (こんにちは) = Hello / Good day\n   - Ohayou gozaimasu (おはようございます) = Good morning\n\n"
                "2. Courtesies:\n   - Arigatou (ありがとう) = Thank you\n   - Onegaishimasu (お願いします) = Please\n   - Douitashimashite (どういたしまして) = You're welcome\n\n"
                "3. Farewells:\n   - Sayounara (さようなら) = Goodbye\n   - Mata ne (またね) = See you later\n\n"
                "4. Basic Responses:\n   - Hai (はい) = Yes\n   - Iie (いいえ) = No"
            ),
            'zh': (
                "Lesson 1: Mandarin Chinese Essentials & Everyday Communication",
                "1. Greetings:\n   - Nǐ hǎo (你好) = Hello\n   - Zǎoshang hǎo (早上好) = Good morning\n\n"
                "2. Courtesies:\n   - Xièxiè (谢谢) = Thank you\n   - Qǐng (请) = Please\n   - Bú kèqì (不客气) = You're welcome\n\n"
                "3. Farewells:\n   - Zàijiàn (再见) = Goodbye\n   - Huí tóu jiàn (回头见) = See you later\n\n"
                "4. Basic Responses:\n   - Shì (是) = Yes\n   - Bù (不) = No"
            ),
            'ko': (
                "Lesson 1: Korean Essentials & Everyday Communication",
                "1. Greetings:\n   - Annyeonghaseyo (안녕하세요) = Hello\n   - Annyeong (안녕) = Hi (Informal)\n\n"
                "2. Courtesies:\n   - Gamsahamnida (감사합니다) = Thank you\n   - Juseyo (주세요) = Please\n   - Cheonman-eyo (천만에요) = You're welcome\n\n"
                "3. Farewells:\n   - Annyeonghi gaseyo (안녕히 가세요) = Goodbye\n\n"
                "4. Basic Responses:\n   - Ye / Ne (예 / 네) = Yes\n   - Aniyo (아니요) = No"
            ),
            'ar': (
                "Lesson 1: Arabic Essentials & Everyday Communication",
                "1. Greetings:\n   - Marhaban (مرحباً) = Hello\n   - Assalamu alaykum (السلام عليكم) = Peace be upon you\n\n"
                "2. Courtesies:\n   - Shukran (شكراً) = Thank you\n   - Min fadlik (من فضلك) = Please\n   - Afwan (عفواً) = You're welcome\n\n"
                "3. Farewells:\n   - Ma'a as-salama (مع السلامة) = Goodbye\n\n"
                "4. Basic Responses:\n   - Na'am (نعم) = Yes\n   - La (لا) = No"
            ),
            'ru': (
                "Lesson 1: Russian Essentials & Everyday Communication",
                "1. Greetings:\n   - Privet (Привет) = Hi (Informal)\n   - Здравствуйте (Zdravstvuyte) = Hello (Formal)\n\n"
                "2. Courtesies:\n   - Spasibo (Спасибо) = Thank you\n   - Pozhaluysta (Пожалуйста) = Please / You're welcome\n\n"
                "3. Farewells:\n   - Do svidaniya (До свидания) = Goodbye\n   - Poka (Пока) = Bye\n\n"
                "4. Basic Responses:\n   - Da (Да) = Yes\n   - Net (Нет) = No"
            ),
            'hi': (
                "Lesson 1: Hindi Essentials & Everyday Communication",
                "1. Greetings:\n   - Namaste (नमस्ते) = Hello / Greetings\n   - Namaskar (नमस्कार) = Formal greetings\n\n"
                "2. Courtesies:\n   - Dhanyavaad / Shukriya (धन्यवाद / शुक्रिया) = Thank you\n   - Kripya (कृपया) = Please\n\n"
                "3. Farewells:\n   - Alvida (अलविदा) = Goodbye\n   - Phir milenge (फिर मिलेंगे) = See you again\n\n"
                "4. Basic Responses:\n   - Haan (हाँ) = Yes\n   - Nahin (नहीं) = No"
            ),
            'nl': (
                "Lesson 1: Dutch Essentials & Everyday Communication",
                "1. Greetings:\n   - Hallo = Hello\n   - Goedemorgen = Good morning\n\n"
                "2. Courtesies:\n   - Dank je / Dank u = Thank you\n   - Alstublieft = Please / You're welcome\n\n"
                "3. Farewells:\n   - Tot ziens = Goodbye\n   - Doei = Bye\n\n"
                "4. Basic Responses:\n   - Ja = Yes\n   - Nee = No"
            ),
            'tr': (
                "Lesson 1: Turkish Essentials & Everyday Communication",
                "1. Greetings:\n   - Merhaba = Hello\n   - Günaydın = Good morning\n\n"
                "2. Courtesies:\n   - Teşekkür ederim = Thank you\n   - Lütfen = Please\n   - Rica ederim = You're welcome\n\n"
                "3. Farewells:\n   - Hoşçakalın = Goodbye\n   - Görüşürüz = See you\n\n"
                "4. Basic Responses:\n   - Evet = Yes\n   - Hayır = No"
            ),
            'pl': (
                "Lesson 1: Polish Essentials & Everyday Communication",
                "1. Greetings:\n   - Cześć = Hello / Hi\n   - Dzień dobry = Good day\n\n"
                "2. Courtesies:\n   - Dziękuję = Thank you\n   - Proszę = Please / You're welcome\n\n"
                "3. Farewells:\n   - Do widzenia = Goodbye\n   - Pa = Bye\n\n"
                "4. Basic Responses:\n   - Tak = Yes\n   - Nie = No"
            ),
            'sv': (
                "Lesson 1: Swedish Essentials & Everyday Communication",
                "1. Greetings:\n   - Hej = Hello\n   - God morgon = Good morning\n\n"
                "2. Courtesies:\n   - Tack = Thank you\n   - Snälla = Please\n   - Ingen sak = You're welcome\n\n"
                "3. Farewells:\n   - Hej då = Goodbye\n   - Vi ses = See you\n\n"
                "4. Basic Responses:\n   - Ja = Yes\n   - Nej = No"
            ),
            'el': (
                "Lesson 1: Greek Essentials & Everyday Communication",
                "1. Greetings:\n   - Geia sou (Γεια σου) = Hello / Hi\n   - Kalimera (Καλημέρα) = Good morning\n\n"
                "2. Courtesies:\n   - Efcharisto (Ευχαριστώ) = Thank you\n   - Parakalo (Παρακαλώ) = Please\n\n"
                "3. Farewells:\n   - Antio (Αντίο) = Goodbye\n   - Ta leme (Τα λέμε) = See you\n\n"
                "4. Basic Responses:\n   - Nai (Ναι) = Yes\n   - Ochi (Όχι) = No"
            ),
            'vi': (
                "Lesson 1: Vietnamese Essentials & Everyday Communication",
                "1. Greetings:\n   - Xin chào = Hello\n   - Chào buổi sáng = Good morning\n\n"
                "2. Courtesies:\n   - Cảm ơn = Thank you\n   - Làm ơn = Please\n   - Không có gì = You're welcome\n\n"
                "3. Farewells:\n   - Tạm biệt = Goodbye\n   - Hẹn gặp lại = See you again\n\n"
                "4. Basic Responses:\n   - Vâng / Dạ = Yes\n   - Không = No"
            ),
            'id': (
                "Lesson 1: Indonesian Essentials & Everyday Communication",
                "1. Greetings:\n   - Halo = Hello\n   - Selamat pagi = Good morning\n\n"
                "2. Courtesies:\n   - Terima kasih = Thank you\n   - Tolong = Please\n   - Sama-sama = You're welcome\n\n"
                "3. Farewells:\n   - Sampai jumpa = Goodbye\n   - Dah = Bye\n\n"
                "4. Basic Responses:\n   - Ya = Yes\n   - Tidak = No"
            ),
            'sw': (
                "Lesson 1: Swahili Essentials & Everyday Communication",
                "1. Greetings:\n   - Jambo / Hujambo = Hello\n   - Habari za asubuhi = Good morning\n\n"
                "2. Courtesies:\n   - Asante = Thank you\n   - Tafadhali = Please\n   - Karibu = You're welcome\n\n"
                "3. Farewells:\n   - Kwaheri = Goodbye\n   - Tutaonana = See you later\n\n"
                "4. Basic Responses:\n   - Ndiyo = Yes\n   - Hapana = No"
            ),
            'he': (
                "Lesson 1: Hebrew Essentials & Everyday Communication",
                "1. Greetings:\n   - Shalom (שלום) = Hello / Peace\n   - Boker tov (בוקר טוב) = Good morning\n\n"
                "2. Courtesies:\n   - Toda (תודה) = Thank you\n   - Bevakasha (בבקשה) = Please / You're welcome\n\n"
                "3. Farewells:\n   - Lehitraot (להתראות) = Goodbye\n\n"
                "4. Basic Responses:\n   - Ken (כן) = Yes\n   - Lo (לא) = No"
            )
        }
        
        for lang in all_langs:
            lang_id = lang['id']
            code = lang['code']
            lang_name = lang['name']
            
            title, content = vocab_samples.get(code, (f"Lesson 1: {lang_name} Essentials", f"1. Hello = Core Greeting\n2. Thank You = Expression of Gratitude"))
            cursor.execute("INSERT INTO lessons (language_id, title, content) VALUES (?, ?, ?)", (lang_id, title, content))

    # Seed Native Quiz Questions for ALL 20 languages if quiz table is empty
    cursor.execute("SELECT COUNT(*) FROM quiz")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, code, name FROM languages")
        all_langs = cursor.fetchall()
        
        quiz_samples = {
            'fr': [
                ("What is the French translation for 'Hello'?", "Au revoir", "Bonjour", "Merci", "Oui", "Bonjour", "'Bonjour' is hello in French."),
                ("How do you say 'Thank you' in French?", "S'il vous plaît", "Bonjour", "Merci", "Au revoir", "Merci", "'Merci' means thank you."),
                ("What is the French word for 'Goodbye'?", "Bonjour", "Au revoir", "Oui", "Non", "Au revoir", "'Au revoir' means goodbye."),
                ("How do you say 'Yes' in French?", "Non", "Oui", "Peut-être", "Merci", "Oui", "'Oui' means yes."),
                ("What is the French translation for 'Please'?", "Merci", "Bonjour", "S'il vous plaît", "Au revoir", "S'il vous plaît", "'S'il vous plaît' means please.")
            ],
            'es': [
                ("What is the Spanish translation for 'Hello'?", "Adiós", "Hola", "Gracias", "Sí", "Hola", "'Hola' is the standard Spanish word for hello."),
                ("How do you say 'Thank you' in Spanish?", "Por favor", "Hola", "Gracias", "Adiós", "Gracias", "'Gracias' means thank you in Spanish."),
                ("What is the Spanish word for 'Goodbye'?", "Adiós", "Hola", "Sí", "No", "Adiós", "'Adiós' is used to say goodbye."),
                ("How do you say 'Good morning' in Spanish?", "Buenas noches", "Buenas tardes", "Buenos días", "Hola", "Buenos días", "'Buenos días' is used in the morning."),
                ("What is the Spanish translation for 'Please'?", "Por favor", "Gracias", "Sí", "No", "Por favor", "'Por favor' means please.")
            ],
            'de': [
                ("What is the German translation for 'Hello'?", "Tschüss", "Hallo", "Danke", "Ja", "Hallo", "'Hallo' is hello in German."),
                ("How do you say 'Thank you' in German?", "Bitte", "Hallo", "Danke", "Nein", "Danke", "'Danke' means thank you."),
                ("What is the German word for 'Goodbye'?", "Hallo", "Auf Wiedersehen", "Ja", "Nein", "Auf Wiedersehen", "'Auf Wiedersehen' means goodbye."),
                ("How do you say 'Yes' in German?", "Nein", "Ja", "Danke", "Bitte", "Ja", "'Ja' means yes."),
                ("What is the German translation for 'Please'?", "Danke", "Bitte", "Hallo", "Tschüss", "Bitte", "'Bitte' means please.")
            ],
            'it': [
                ("What is the Italian word for 'Hello'?", "Arrivederci", "Ciao", "Grazie", "Sì", "Ciao", "'Ciao' is the common Italian greeting meaning hello or hi."),
                ("How do you say 'Thank you' in Italian?", "Prego", "Per favore", "Grazie", "Ciao", "Grazie", "'Grazie' translates to thank you in Italian."),
                ("What does 'Buongiorno' mean?", "Good night", "Good morning", "Goodbye", "Please", "Good morning", "'Buongiorno' means good morning."),
                ("What is the Italian word for 'Goodbye'?", "Ciao", "Arrivederci", "Sì", "No", "Arrivederci", "'Arrivederci' means goodbye."),
                ("What is the Italian word for 'Yes'?", "No", "Sì", "Grazie", "Prego", "Sì", "'Sì' means yes in Italian.")
            ],
            'pt': [
                ("What is the Portuguese word for 'Hello'?", "Adeus", "Olá", "Obrigado", "Sim", "Olá", "'Olá' is the standard Portuguese greeting for hello."),
                ("How do you say 'Thank you' in Portuguese?", "Por favor", "Obrigado", "Olá", "Adeus", "Obrigado", "'Obrigado' means thank you."),
                ("What is the Portuguese word for 'Goodbye'?", "Olá", "Sim", "Adeus", "Não", "Adeus", "'Adeus' means goodbye."),
                ("What is the Portuguese word for 'Yes'?", "Não", "Sim", "Talvez", "Por favor", "Sim", "'Sim' means yes."),
                ("How do you say 'Please' in Portuguese?", "Obrigado", "Por favor", "Adeus", "Olá", "Por favor", "'Por favor' means please.")
            ],
            'ja': [
                ("What is the Japanese greeting for 'Hello'?", "Sayounara", "Konnichiwa", "Arigatou", "Hai", "Konnichiwa", "'Konnichiwa' is the standard daytime greeting."),
                ("How do you say 'Thank you' in Japanese?", "Arigatou", "Onegaishimasu", "Sayounara", "Iie", "Arigatou", "'Arigatou' means thank you."),
                ("What does 'Sayounara' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Sayounara' means goodbye."),
                ("What is the Japanese word for 'Yes'?", "Iie", "Hai", "Arigatou", "Onegaishimasu", "Hai", "'Hai' means yes."),
                ("What is the Japanese word for 'Please'?", "Arigatou", "Onegaishimasu", "Konnichiwa", "Sayounara", "Onegaishimasu", "'Onegaishimasu' is used for making polite requests.")
            ],
            'zh': [
                ("What is the Mandarin Chinese greeting for 'Hello'?", "Zàijiàn", "Nǐ hǎo", "Xièxiè", "Shì", "Nǐ hǎo", "'Nǐ hǎo' means hello."),
                ("How do you say 'Thank you' in Mandarin?", "Xièxiè", "Qǐng", "Zàijiàn", "Bù", "Xièxiè", "'Xièxiè' means thank you."),
                ("What does 'Zàijiàn' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Zàijiàn' means goodbye."),
                ("What is the Mandarin word for 'Yes'?", "Bù", "Shì", "Xièxiè", "Qǐng", "Shì", "'Shì' means yes / to be."),
                ("What is the Mandarin word for 'Please'?", "Xièxiè", "Qǐng", "Zàijiàn", "Nǐ hǎo", "Qǐng", "'Qǐng' means please.")
            ],
            'ko': [
                ("What is the Korean greeting for 'Hello'?", "Annyeonghi gaseyo", "Annyeonghaseyo", "Gamsahamnida", "Ye", "Annyeonghaseyo", "'Annyeonghaseyo' is the standard polite greeting."),
                ("How do you say 'Thank you' in Korean?", "Juseyo", "Gamsahamnida", "Annyeonghaseyo", "Aniyo", "Gamsahamnida", "'Gamsahamnida' expresses gratitude."),
                ("What does 'Annyeonghi gaseyo' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "Said to someone leaving, meaning goodbye."),
                ("What is the Korean word for 'Yes'?", "Aniyo", "Ye", "Juseyo", "Gamsahamnida", "Ye", "'Ye' or 'Ne' means yes."),
                ("What is the Korean word for 'Please'?", "Gamsahamnida", "Juseyo", "Annyeonghaseyo", "Ye", "Juseyo", "'Juseyo' means please.")
            ],
            'ar': [
                ("What is the Arabic greeting for 'Hello'?", "Ma'a as-salama", "Marhaban", "Shukran", "Na'am", "Marhaban", "'Marhaban' means hello or welcome."),
                ("How do you say 'Thank you' in Arabic?", "Shukran", "Min fadlik", "Marhaban", "La", "Shukran", "'Shukran' means thank you."),
                ("What does 'Ma'a as-salama' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Ma'a as-salama' means goodbye."),
                ("What is the Arabic word for 'Yes'?", "La", "Na'am", "Shukran", "Afwan", "Na'am", "'Na'am' means yes."),
                ("What is the Arabic word for 'Please'?", "Shukran", "Min fadlik", "Marhaban", "La", "Min fadlik", "'Min fadlik' means please.")
            ],
            'ru': [
                ("What is the Russian greeting for 'Hello' (formal)?", "Poka", "Zdravstvuyte", "Spasibo", "Da", "Zdravstvuyte", "'Zdravstvuyte' is the formal hello."),
                ("How do you say 'Thank you' in Russian?", "Pozhaluysta", "Spasibo", "Privet", "Net", "Spasibo", "'Spasibo' means thank you."),
                ("What does 'Do svidaniya' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Do svidaniya' means goodbye."),
                ("What is the Russian word for 'Yes'?", "Net", "Da", "Spasibo", "Pozhaluysta", "Da", "'Da' means yes."),
                ("What is the Russian word for 'Please'?", "Spasibo", "Pozhaluysta", "Privet", "Poka", "Pozhaluysta", "'Pozhaluysta' means please / you're welcome.")
            ],
            'hi': [
                ("What is the Hindi greeting for 'Hello'?", "Alvida", "Namaste", "Dhanyavaad", "Haan", "Namaste", "'Namaste' is the traditional greeting."),
                ("How do you say 'Thank you' in Hindi?", "Kripya", "Dhanyavaad", "Namaste", "Nahin", "Dhanyavaad", "'Dhanyavaad' means thank you."),
                ("What does 'Alvida' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Alvida' means goodbye."),
                ("What is the Hindi word for 'Yes'?", "Nahin", "Haan", "Dhanyavaad", "Kripya", "Haan", "'Haan' means yes."),
                ("What is the Hindi word for 'Please'?", "Dhanyavaad", "Kripya", "Namaste", "Haan", "Kripya", "'Kripya' means please.")
            ],
            'nl': [
                ("What is the Dutch word for 'Hello'?", "Tot ziens", "Hallo", "Dank je", "Ja", "Hallo", "'Hallo' means hello."),
                ("How do you say 'Thank you' in Dutch?", "Alstublieft", "Hallo", "Dank je", "Nee", "Dank je", "'Dank je' means thank you."),
                ("What does 'Tot ziens' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Tot ziens' means goodbye."),
                ("What is the Dutch word for 'Yes'?", "Nee", "Ja", "Dank je", "Alstublieft", "Ja", "'Ja' means yes."),
                ("What is the Dutch word for 'Please'?", "Dank je", "Alstublieft", "Hallo", "Tot ziens", "Alstublieft", "'Alstublieft' means please.")
            ],
            'tr': [
                ("What is the Turkish word for 'Hello'?", "Hoşçakalın", "Merhaba", "Teşekkür ederim", "Evet", "Merhaba", "'Merhaba' means hello."),
                ("How do you say 'Thank you' in Turkish?", "Lütfen", "Merhaba", "Teşekkür ederim", "Hayır", "Teşekkür ederim", "'Teşekkür ederim' means thank you."),
                ("What does 'Hoşçakalın' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Hoşçakalın' means goodbye."),
                ("What is the Turkish word for 'Yes'?", "Hayır", "Evet", "Teşekkür ederim", "Lütfen", "Evet", "'Evet' means yes."),
                ("What is the Turkish word for 'Please'?", "Teşekkür ederim", "Lütfen", "Merhaba", "Evet", "Lütfen", "'Lütfen' means please.")
            ],
            'pl': [
                ("What is the Polish word for 'Hello'?", "Do widzenia", "Cześć", "Dziękuję", "Tak", "Cześć", "'Cześć' means hello or hi."),
                ("How do you say 'Thank you' in Polish?", "Proszę", "Dziękuję", "Cześć", "Nie", "Dziękuję", "'Dziękuję' means thank you."),
                ("What does 'Do widzenia' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Do widzenia' means goodbye."),
                ("What is the Polish word for 'Yes'?", "Nie", "Tak", "Dziękuję", "Proszę", "Tak", "'Tak' means yes."),
                ("What is the Polish word for 'Please'?", "Dziękuję", "Proszę", "Cześć", "Tak", "Proszę", "'Proszę' means please.")
            ],
            'sv': [
                ("What is the Swedish word for 'Hello'?", "Hej då", "Hej", "Tack", "Ja", "Hej", "'Hej' means hello."),
                ("How do you say 'Thank you' in Swedish?", "Snälla", "Hej", "Tack", "Nej", "Tack", "'Tack' means thank you."),
                ("What does 'Hej då' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Hej då' means goodbye."),
                ("What is the Swedish word for 'Yes'?", "Nej", "Ja", "Tack", "Snälla", "Ja", "'Ja' means yes."),
                ("What is the Swedish word for 'Please'?", "Tack", "Snälla", "Hej", "Ja", "Snälla", "'Snälla' means please.")
            ],
            'el': [
                ("What is the Greek word for 'Hello'?", "Antio", "Geia sou", "Efcharisto", "Nai", "Geia sou", "'Geia sou' means hello."),
                ("How do you say 'Thank you' in Greek?", "Parakalo", "Geia sou", "Efcharisto", "Ochi", "Efcharisto", "'Efcharisto' means thank you."),
                ("What does 'Antio' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Antio' means goodbye."),
                ("What is the Greek word for 'Yes'?", "Ochi", "Nai", "Efcharisto", "Parakalo", "Nai", "'Nai' means yes."),
                ("What is the Greek word for 'Please'?", "Efcharisto", "Parakalo", "Geia sou", "Nai", "Parakalo", "'Parakalo' means please.")
            ],
            'vi': [
                ("What is the Vietnamese word for 'Hello'?", "Tạm biệt", "Xin chào", "Cảm ơn", "Vâng", "Xin chào", "'Xin chào' means hello."),
                ("How do you say 'Thank you' in Vietnamese?", "Làm ơn", "Xin chào", "Cảm ơn", "Không", "Cảm ơn", "'Cảm ơn' means thank you."),
                ("What does 'Tạm biệt' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Tạm biệt' means goodbye."),
                ("What is the Vietnamese word for 'Yes'?", "Không", "Vâng", "Cảm ơn", "Xin chào", "Vâng", "'Vâng' or 'Dạ' means yes."),
                ("What is the Vietnamese word for 'Please'?", "Cảm ơn", "Làm ơn", "Xin chào", "Tạm biệt", "Làm ơn", "'Làm ơn' means please.")
            ],
            'id': [
                ("What is the Indonesian word for 'Hello'?", "Sampai jumpa", "Halo", "Terima kasih", "Ya", "Halo", "'Halo' means hello."),
                ("How do you say 'Thank you' in Indonesian?", "Tolong", "Halo", "Terima kasih", "Tidak", "Terima kasih", "'Terima kasih' means thank you."),
                ("What does 'Sampai jumpa' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Sampai jumpa' means goodbye."),
                ("What is the Indonesian word for 'Yes'?", "Tidak", "Ya", "Terima kasih", "Tolong", "Ya", "'Ya' means yes."),
                ("What is the Indonesian word for 'Please'?", "Terima kasih", "Tolong", "Halo", "Ya", "Tolong", "'Tolong' means please.")
            ],
            'sw': [
                ("What is the Swahili word for 'Hello'?", "Kwaheri", "Jambo", "Asante", "Ndiyo", "Jambo", "'Jambo' is a standard Swahili greeting."),
                ("How do you say 'Thank you' in Swahili?", "Tafadhali", "Jambo", "Asante", "Hapana", "Asante", "'Asante' means thank you."),
                ("What does 'Kwaheri' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Kwaheri' means goodbye."),
                ("What is the Swahili word for 'Yes'?", "Hapana", "Ndiyo", "Asante", "Tafadhali", "Ndiyo", "'Ndiyo' means yes."),
                ("What is the Swahili word for 'Please'?", "Asante", "Tafadhali", "Jambo", "Ndiyo", "Tafadhali", "'Tafadhali' means please.")
            ],
            'he': [
                ("What is the Hebrew word for 'Hello'?", "Lehitraot", "Shalom", "Toda", "Ken", "Shalom", "'Shalom' means hello or peace."),
                ("How do you say 'Thank you' in Hebrew?", "Bevakasha", "Shalom", "Toda", "Lo", "Toda", "'Toda' means thank you."),
                ("What does 'Lehitraot' mean?", "Hello", "Thank you", "Goodbye", "Yes", "Goodbye", "'Lehitraot' means goodbye."),
                ("What is the Hebrew word for 'Yes'?", "Lo", "Ken", "Toda", "Bevakasha", "Ken", "'Ken' means yes."),
                ("What is the Hebrew word for 'Please'?", "Toda", "Bevakasha", "Shalom", "Ken", "Bevakasha", "'Bevakasha' means please or you're welcome.")
            ]
        }
        
        for lang in all_langs:
            lang_id = lang['id']
            code = lang['code']
            lang_name = lang['name']
            
            if code in quiz_samples:
                questions = [(lang_id, q[0], q[1], q[2], q[3], q[4], q[5], q[6]) for q in quiz_samples[code]]
            else:
                questions = [
                    (lang_id, f"What is a standard greeting in {lang_name}?", "Farewell", "Hello", "Thanks", "Please", "Hello", f"This is the core greeting phrase used in {lang_name}."),
                    (lang_id, f"How do you express gratitude in {lang_name}?", "Thank you", "Sorry", "Goodbye", "Yes", "Thank you", f"Gratitude is expressed using this term in {lang_name}."),
                    (lang_id, f"What is a parting phrase ('Goodbye') in {lang_name}?", "Hello", "Goodbye", "No", "Yes", "Goodbye", f"This is the standard parting word in {lang_name}.")
                ]
                
            cursor.executemany("""
                INSERT INTO quiz (language_id, question, option_a, option_b, option_c, option_d, answer, explanation) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, questions)
        
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