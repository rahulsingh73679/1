# SmartPrep IITM - Exam Preparation Platform

A comprehensive Streamlit-based web application for IITM students to practice exams, calculate grades, and evaluate response sheets.

## Features

1. **Practice Papers**: Select subjects and papers to practice in Practice Mode or Exam Mode
2. **Grade Calculator**: Calculate your grades based on various assessment scores for Foundational and Diploma level courses
3. **Response Sheet Evaluator**: Upload answer keys and response sheets to automatically evaluate your performance
4. **Guidelines**: Comprehensive instructions on how to use the platform

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The application requires a SQLite database. Run the setup script to create the database with sample data:

```bash
python setup_database.py
```

This will create `database.db` with sample subjects, papers, and questions.

### 3. Run the Application

```bash
streamlit run 1_Home.py
```

The application will open in your default web browser at `http://localhost:8501`

## Project Structure

```
smartiitm-main/
├── 1_Home.py                          # Main home page
├── pages/
│   ├── 2_Grade_Calculator_[Beta].py  # Grade calculator
│   ├── 3_Response_Sheet_Evaluator_[Beta].py  # Response sheet evaluator
│   └── 4_Guidelines.py                # Guidelines page
├── database.db                        # SQLite database (created by setup script)
├── setup_database.py                  # Database initialization script
├── requirements.txt                   # Python dependencies
├── page_views.txt                    # Page view counter
└── page_reviews.txt                  # Page reviews storage
```

## Database Schema

- **Subjects**: List of available subjects
- **Paper**: Exam papers with metadata
- **Question**: Questions with answers, marks, and types (MCQ/MSQ/SA)
- **Options**: Multiple choice options for questions
- **Comprehension**: Comprehension passages for questions
- **Image**: Image data stored as BLOB

## Usage

### Practice Mode
1. Select a subject from the dropdown
2. Choose a paper
3. Select "Practice Mode"
4. Answer questions and click "Show Answer" to see correct answers

### Exam Mode
1. Select a subject and paper
2. Select "Exam Mode"
3. Answer all questions
4. Click "Submit" to see your score and detailed feedback

### Grade Calculator
1. Navigate to "Grade Calculator" from the sidebar
2. Select your level (Foundational/Diploma)
3. Select your subject
4. Enter your scores for various assessments
5. Click "Submit" to see your calculated grade

### Response Sheet Evaluator
1. Navigate to "Response Sheet Evaluator" from the sidebar
2. Upload your answer key PDF
3. Upload your response sheet PDF
4. View your score breakdown by subject

## Notes

- The database file (`database.db`) is a Git LFS file. Run `setup_database.py` to create a working database.
- Some features may require additional data in the database to function properly.
- The application uses Streamlit's session state to manage user interactions.

## Troubleshooting

- If you see "No subjects found", run `python setup_database.py` to initialize the database
- If images don't display, ensure the Image table has proper BLOB data
- For PDF evaluation issues, ensure PDFs are in the correct format as described in the Guidelines

## Credits

Grade Calculator credits: Sai Prakash BVC
