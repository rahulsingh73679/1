# Removed Packages Documentation

This file documents packages that were in the original requirements.txt but are NOT actually used in the codebase. They were removed to fix Streamlit Cloud deployment issues.

## Why Packages Were Removed

The original `requirements.txt` contained **89 packages**, many of which were:
- **Not actually used** in the codebase
- **Very large** (torch, torchvision = ~2GB+)
- **Causing dependency conflicts**
- **Timing out** during installation on Streamlit Cloud

## Removed Packages

### Large ML/AI Packages (Not Used)
- `torch`, `torchvision` (very large, ~2GB+, not used)
- `transformers`, `sentence-transformers` (not used)
- `langchain`, `langsmith` (not used)
- `faiss-cpu` (not used)
- `huggingface-hub` (not used)
- `nltk` (not used)
- `scikit-learn`, `scipy` (not used)
- `openai` (not used)
- And many other ML/AI dependencies

## Current Minimal Requirements

The current `requirements.txt` only includes packages actually used:

- `streamlit` - Web framework (required)
- `PyPDF2` - PDF reading (used in Response Sheet Evaluator)
- `pandas` - Data manipulation (used in Response Sheet Evaluator)
- `pdfminer.six` - PDF parsing (used in Response Sheet Evaluator)

## If You Need These Packages

If you need any of these packages in the future:
1. Add them back to `requirements.txt`
2. Ensure they're actually imported and used in the code
3. Be aware that large packages like `torch` may cause deployment issues

## Note

This file is for documentation only. Streamlit Cloud does NOT process this file.
