# 🔧 Maintenance Management System

A simple maintenance management system built with Python. The system allows users to report maintenance issues and uses AI to analyze the reported problem.

The goal of this project is to make maintenance issue reporting easier by automatically categorizing issues, determining their priority, and providing a suggested action.

## Features

- Report maintenance issues
- Store maintenance issues in a database
- AI-powered issue analysis
- Automatic issue categorization
- Automatic priority detection
- AI-generated issue summary
- Suggested maintenance action
- Simple and user-friendly Streamlit interface

## Technologies Used

- Python
- Streamlit
- Supabase
- PostgreSQL
- Google Gemini API
- Git
- GitHub

## How It Works

1. The user enters the maintenance issue.
2. The issue title and description are sent to the AI.
3. Google Gemini analyzes the issue.
4. The AI determines the category and priority.
5. The AI generates a short summary and suggested action.
6. The issue and AI results are stored in Supabase.
7. The results are displayed in the Streamlit application.

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
