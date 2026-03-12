#!/bin/bash

# SmartPrep IITM - Run Script

echo "Setting up SmartPrep IITM..."

# Check if database exists, if not create it
if [ ! -f "database.db" ] || [ ! -s "database.db" ]; then
    echo "Database not found or empty. Creating database..."
    python3 setup_database.py
fi

# Check if page_views.txt exists
if [ ! -f "page_views.txt" ]; then
    echo "0" > page_views.txt
fi

# Check if page_reviews.txt exists
if [ ! -f "page_reviews.txt" ]; then
    echo " -- " > page_reviews.txt
fi

echo "Starting Streamlit application..."
streamlit run 1_Home.py
