# SmartPrep IITM - Setup and Usage Guide

## What Has Been Fixed

### 1. Database Issues
- **Problem**: The `database.db` file was a Git LFS pointer, not an actual database
- **Solution**: Created `setup_database.py` script that creates a proper SQLite database with sample data
- **Tables Created**: Subjects, Paper, Question, Options, Comprehension, Image

### 2. Grade Calculator Bugs
- **Problem**: Variables like Q1, Q2, OP1, OP2, etc. were not initialized in all code paths, causing NameError
- **Solution**: 
  - Initialized all variables with default values (-1 for "not attempted")
  - Fixed conditional logic bugs (e.g., `if(OP1 or OP2 >= 30)` → `if(OP1_calc >= 30 or OP2_calc >= 30)`)
  - Added proper handling for -1 values (not attempted) by converting to 0 for calculations
  - Fixed min_value constraints to allow -1 for "not attempted" inputs

### 3. Response Sheet Evaluator Issues
- **Problem**: Variable initialization issues and undefined variables
- **Solution**: 
  - Removed unnecessary `declarers` flag pattern
  - Properly initialized all variables at the start
  - Fixed undefined `subject` and `clean` variables

### 4. Home Page Improvements
- **Problem**: No error handling for empty database
- **Solution**: Added checks for empty subjects/papers/questions with user-friendly warnings

## Quick Start

### Option 1: Using the Run Script (Recommended)
```bash
./run_app.sh
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create database
python setup_database.py

# 3. Run application
streamlit run 1_Home.py
```

## Application Structure

### Main Pages

1. **Home (1_Home.py)**
   - Subject selection
   - Paper selection
   - Practice Mode / Exam Mode
   - Question display and answer checking

2. **Grade Calculator (pages/2_Grade_Calculator_[Beta].py)**
   - Foundational level grade calculation
   - Diploma level grade calculation
   - Subject-specific grading formulas

3. **Response Sheet Evaluator (pages/3_Response_Sheet_Evaluator_[Beta].py)**
   - PDF answer key upload
   - PDF response sheet upload
   - Automatic score calculation

4. **Guidelines (pages/4_Guidelines.py)**
   - Usage instructions
   - Troubleshooting tips

## Database Schema

The database contains the following tables:

- **Subjects**: List of available subjects
- **Paper**: Exam papers with metadata (paperid, papername, subjects, exam, paperterm)
- **Question**: Questions with answers, marks, and types (MCQ/MSQ/SA)
- **Options**: Multiple choice options for questions
- **Comprehension**: Comprehension passages for questions
- **Image**: Image data stored as BLOB

## Sample Data

The setup script creates sample data including:
- 4 sample subjects
- 2 sample papers
- 3 sample questions (MCQ and SA types)
- 8 sample options

You can extend this by modifying `setup_database.py` or directly inserting data into the database.

## Testing the Application

1. **Test Home Page**:
   - Select a subject from dropdown
   - Select a paper
   - Try both Practice Mode and Exam Mode
   - Verify questions display correctly

2. **Test Grade Calculator**:
   - Select Foundational level
   - Choose "Mathematics for Data Science 1"
   - Enter sample scores
   - Click Submit to see calculated grade

3. **Test Response Sheet Evaluator**:
   - Upload sample PDF answer key
   - Upload sample PDF response sheet
   - Verify score calculation

## Known Limitations

1. **Database**: Currently uses sample data. For production, you'll need to populate with real exam data
2. **Images**: Image display requires proper BLOB data in the Image table
3. **PDF Format**: Response Sheet Evaluator expects specific PDF formats from IITM dashboard

## Troubleshooting

### "No subjects found"
- Run `python setup_database.py` to create the database

### "Database error"
- Ensure `database.db` is a valid SQLite file (not Git LFS pointer)
- Delete `database.db` and run `setup_database.py` again

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`

### Grade Calculator shows errors
- Ensure all required fields are filled
- Use -1 for "not attempted" fields
- Check that subject-specific fields are entered

## Next Steps

1. **Populate Real Data**: Replace sample data with actual exam papers and questions
2. **Add Images**: Upload question images to the Image table
3. **Enhance UI**: Improve styling and user experience
4. **Add Features**: Consider adding user authentication, progress tracking, etc.

## Support

For issues or questions, refer to the Guidelines page in the application or check the code comments.
