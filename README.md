# Maintenance Management System

A simple maintenance management system built with Python that allows users to report maintenance issues and uses AI to analyze them.

The main purpose of this project is to make it easier to record maintenance problems, categorize them, assign a priority, and get an initial recommendation for dealing with the issue.

## Features

- Report maintenance issues
- Store issues in a database
- AI-based issue analysis
- Automatic issue categorization
- Automatic priority detection
- AI-generated issue summary
- Suggested action for maintenance staff
- Simple web interface using Streamlit

## Technologies Used

- Python
- Streamlit
- Supabase
- PostgreSQL
- Google Gemini API
- Git & GitHub

## How It Works

The basic workflow of the system is:

1. User enters the maintenance issue.
2. The issue title and description are sent to the AI.
3. Gemini analyzes the issue.
4. The system gets information such as category and priority.
5. The issue and AI results are stored in Supabase.
6. The result is shown to the user through the Streamlit interface.

## Project Structure

```text
Maintenance System/
│
├── assets/
│
├── services/
│   ├── ai_service.py
│   └── database.py
│
├── utils/
│
├── app.py
├── test_connection.py
├── test_gemini.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
