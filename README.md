# FacilityFlow — AI-Assisted Maintenance Management System

FacilityFlow is a web-based maintenance management application built with Python and Streamlit. It helps organize maintenance requests, analyze reported issues using Google Gemini AI, track issue progress, and monitor maintenance activity through a dashboard.

The goal of FacilityFlow is to make maintenance reporting and tracking more organized by providing AI-assisted issue analysis, centralized issue management, and useful analytics in one place.

## Features

### Maintenance Issue Reporting
- Submit maintenance issues with a title, description, and location.
- Analyze reported problems using Google Gemini AI.
- Generate suggested categories, priority levels, summaries, and recommended actions.

### AI-Assisted Analysis
- Uses the Google Gemini API to analyze maintenance issue details.
- Provides an AI-generated issue summary and suggested action.
- Validates AI responses before using the analysis.

### Issue Management
- View and manage maintenance issues in one place.
- Search issues by title, description, and location.
- Filter issues using available categories, priorities, statuses, departments, and technicians.
- Assign technicians and update issue statuses.
- Track issues through Open, In Progress, and Resolved states.

### Dashboard & Analytics
- View key maintenance metrics.
- Monitor open, high-priority, and resolved issues.
- Visualize issue distribution using charts.
- Review maintenance activity and progress.

### Error Handling & Testing
- Handles database and AI-related errors.
- Includes automated tests for important application functionality.
- Supports testing of application logic and integrations.

## Technologies Used

- **Python** — Core application logic
- **Streamlit** — Web application interface
- **Supabase** — Database service and application data storage
- **PostgreSQL** — Relational database used by Supabase
- **Google Gemini API** — AI-assisted issue analysis
- **Pandas** — Data handling and processing
- **Plotly** — Interactive charts and visualizations
- **Pytest** — Automated testing
- **Git & GitHub** — Version control and source code hosting

## How It Works

1. A user submits a maintenance issue through the application.
2. The application uses Google Gemini to analyze the issue details.
3. The AI suggests a category, priority, summary, and recommended action.
4. The application validates the AI response.
5. The issue and relevant analysis are stored in Supabase.
6. Users can search, filter, assign, and update maintenance issues.
7. The dashboard and analytics display an overview of maintenance activity.

## Project Structure

```text
FacilityFlow/
├── assets/                 # Application assets and styling resources
├── services/               # External service integrations
│   ├── ai_service.py       # Google Gemini AI integration
│   └── database.py         # Database connection setup
├── utils/
│   ├── repository.py       # Data access operations
│   ├── logic.py            # Application logic and calculations
│   └── theme.py            # UI theme and chart styling
├── tests/                  # Automated tests
├── app.py                  # Main Streamlit application
├── requirements.txt        # Application dependencies
├── requirements-dev.txt    # Development and testing dependencies
├── .env.example            # Example environment configuration
├── .gitignore              # Git exclusion rules
└── README.md               # Project documentation
```

*Note: The structure above describes the expected organization. Update it if the actual files in your latest project folder differ.*

## Getting Started

### Prerequisites

- Python 3.10 or a compatible Python version
- A Supabase project
- A Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/Sohaib313914/Maintenance-Management-System.git
cd Maintenance-Management-System
```

### 2. Create and Activate a Virtual Environment

**Windows PowerShell:**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

For development and testing dependencies, run:

```bash
python -m pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory and add your own credentials:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder values with your own credentials. Never commit your actual API keys or secrets to GitHub.

### 5. Run the Application

```bash
python -m streamlit run app.py
```

The application will provide a local URL in the terminal, usually `http://localhost:8501`.

## Running Tests

Run the automated test suite with:

```bash
python -m pytest -v
```

Some integration tests may require valid credentials and access to external services. Check the test configuration before running them.

## Security Notes

- Keep your `.env` file private.
- Never publish API keys, passwords, or database credentials.
- Use `.env.example` to document the required environment variables without exposing their values.
- Review `.gitignore` before pushing the project to GitHub.

## Project Goals

FacilityFlow demonstrates the integration of a web application interface, database operations, AI-assisted analysis, issue tracking, and analytics in a single project.

It is also a learning project focused on practical Python development, API integration, database interaction, application testing, and user interface improvement.

## Author

**Sohaib**

GitHub: [Sohaib313914](https://github.com/Sohaib313914)

---

*FacilityFlow — Organizing maintenance, one issue at a time.*
