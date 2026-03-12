import sqlite3
import os

# Remove the old file if it exists (but keep backup if it's a real database)
if os.path.exists('database.db'):
    # Check if it's a Git LFS pointer file or empty/invalid database
    try:
        # Check file size - if it's very small, it might be a pointer or empty
        if os.path.getsize('database.db') < 1000:
            with open('database.db', 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline()
                if 'version https://git-lfs.github.com' in first_line:
                    print("Detected Git LFS pointer file. Creating new database...")
                    os.remove('database.db')
                else:
                    # Try to open as SQLite to check if valid
                    try:
                        test_conn = sqlite3.connect('database.db')
                        test_conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                        test_conn.close()
                        # If we get here, it's a valid database - don't delete it
                        print("Valid database found. Skipping initialization.")
                        exit(0)
                    except:
                        # Invalid database, remove it
                        print("Invalid database file detected. Creating new database...")
                        os.remove('database.db')
        else:
            # Large file - might be valid database, check it
            try:
                test_conn = sqlite3.connect('database.db')
                test_conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                test_conn.close()
                # Valid database exists
                print("Valid database found. Skipping initialization.")
                exit(0)
            except:
                # Invalid database
                backup_name = 'database.db.backup'
                if not os.path.exists(backup_name):
                    import shutil
                    shutil.copy('database.db', backup_name)
                    print(f"Backed up existing database to {backup_name}")
                os.remove('database.db')
    except Exception as e:
        print(f"Error checking database: {e}. Creating new database...")
        if os.path.exists('database.db'):
            os.remove('database.db')

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create Subjects table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Subjects (
    subjectname TEXT PRIMARY KEY
)
''')

# Create Paper table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Paper (
    paperid TEXT PRIMARY KEY,
    papername TEXT,
    subjects TEXT,
    exam TEXT,
    paperterm TEXT
)
''')

# Create Question table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Question (
    questionid TEXT PRIMARY KEY,
    questiontext TEXT,
    questiontype TEXT,
    answer TEXT,
    imageids TEXT,
    marks REAL,
    compid TEXT,
    paperid TEXT,
    subject TEXT
)
''')

# Create Options table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Options (
    questionid TEXT,
    optnumber INTEGER,
    opttext TEXT,
    answer INTEGER,
    imageids TEXT,
    PRIMARY KEY (questionid, optnumber)
)
''')

# Create Comprehension table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Comprehension (
    compid TEXT PRIMARY KEY,
    comptext TEXT,
    imageids TEXT
)
''')

# Create Image table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Image (
    imageid TEXT PRIMARY KEY,
    image BLOB
)
''')

# Insert sample subjects
subjects = [
    'Mathematics for Data Science 1',
    'Statistics for Data Science 1',
    'Introduction to Python programming',
    'Computational Thinking'
]
for subject in subjects:
    cursor.execute('INSERT OR IGNORE INTO Subjects (subjectname) VALUES (?)', (subject,))

# Insert sample papers
papers = [
    ('PAPER001', 'Sample Quiz 1 Paper', 'Mathematics for Data Science 1', 'Q1', '23T1'),
    ('PAPER002', 'Sample End Term Paper', 'Statistics for Data Science 1', 'ET', '23T2'),
]
for paper in papers:
    cursor.execute('INSERT OR IGNORE INTO Paper (paperid, papername, subjects, exam, paperterm) VALUES (?, ?, ?, ?, ?)', paper)

# Insert sample questions
questions = [
    ('Q001', 'What is 2 + 2?', 'MCQ', '2', '', 2.0, 'NONE', 'PAPER001', 'Mathematics for Data Science 1'),
    ('Q002', 'What is the mean of [1, 2, 3, 4, 5]?', 'MCQ', '3', '', 2.0, 'NONE', 'PAPER002', 'Statistics for Data Science 1'),
    ('Q003', 'Explain the concept of variables in Python.', 'SA', 'Variables are containers for storing data values', '', 5.0, 'NONE', 'PAPER001', 'Introduction to Python programming'),
]
for q in questions:
    cursor.execute('INSERT OR IGNORE INTO Question (questionid, questiontext, questiontype, answer, imageids, marks, compid, paperid, subject) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', q)

# Insert sample options
options = [
    ('Q001', 1, '3', 0, ''),
    ('Q001', 2, '4', 1, ''),
    ('Q001', 3, '5', 0, ''),
    ('Q001', 4, '6', 0, ''),
    ('Q002', 1, '2', 0, ''),
    ('Q002', 2, '2.5', 0, ''),
    ('Q002', 3, '3', 1, ''),
    ('Q002', 4, '3.5', 0, ''),
]
for opt in options:
    cursor.execute('INSERT OR IGNORE INTO Options (questionid, optnumber, opttext, answer, imageids) VALUES (?, ?, ?, ?, ?)', opt)

conn.commit()
conn.close()
print("Database created successfully!")
