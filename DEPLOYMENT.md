# Streamlit Cloud Deployment Guide

## Issue Fixed

The original `requirements.txt` contained many unused packages including:
- `torch` and `torchvision` (very large, ~2GB+)
- `transformers`, `sentence-transformers` (large ML packages)
- `langchain`, `langsmith` (not used)
- Many other ML/AI dependencies

These packages were causing installation failures on Streamlit Cloud due to:
1. **Size**: Torch alone is several GB
2. **Dependencies**: Complex dependency conflicts
3. **Timeout**: Installation takes too long

## Solution

Created a minimal `requirements.txt` with only packages actually used:
- `streamlit` - Web framework
- `PyPDF2` - PDF reading
- `pandas` - Data manipulation
- `pdfminer.six` - PDF parsing

## Changes Made

1. **Minimal requirements.txt**: Only includes actually used packages
2. **Auto database initialization**: Database is created automatically on first run
3. **Streamlit config**: Added `.streamlit/config.toml` for better deployment

## Deployment Steps

1. **Push to GitHub**: Ensure all files are committed and pushed
   ```bash
   git add .
   git commit -m "Fix requirements.txt for Streamlit Cloud"
   git push
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Connect your GitHub repository
   - Set main file path: `1_Home.py`
   - Click "Deploy"

3. **Verify Deployment**:
   - Check that the app loads without errors
   - Database should initialize automatically
   - Test all features (Practice Mode, Grade Calculator, etc.)

## Troubleshooting

### "Error installing requirements"
- ✅ **Fixed**: Minimal requirements.txt should install quickly
- If still failing, check Streamlit Cloud logs for specific package errors

### "Database not found"
- ✅ **Fixed**: Database auto-initializes on first run
- Check that `setup_database.py` is in the repository

### "Module not found"
- Ensure all imports match the minimal requirements.txt
- Check that you're not importing unused packages

### App loads but shows errors
- Check Streamlit Cloud logs (Manage App → Logs)
- Verify database initialization completed successfully
- Check that all Python files are in the correct locations

## File Structure for Streamlit Cloud

```
your-repo/
├── 1_Home.py                    # Main entry point
├── pages/
│   ├── 2_Grade_Calculator_[Beta].py
│   ├── 3_Response_Sheet_Evaluator_[Beta].py
│   └── 4_Guidelines.py
├── setup_database.py           # Database initialization
├── requirements.txt            # Minimal dependencies
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── database.db                 # Will be created automatically
├── page_views.txt             # Will be created automatically
└── page_reviews.txt           # Will be created automatically
```

## Notes

- The database (`database.db`) will be created automatically on first run
- If you need to reset the database, delete it and redeploy
- All data is stored in the Streamlit Cloud instance (ephemeral)
- For persistent data, consider using Streamlit's secrets or external database

## Support

If deployment still fails:
1. Check Streamlit Cloud logs for specific errors
2. Verify all files are in the repository
3. Ensure Python version compatibility (Streamlit Cloud uses Python 3.9+)
4. Check that `requirements.txt` syntax is correct (no extra spaces, correct versions)
