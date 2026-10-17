# FacilityFlow

FacilityFlow is a facility maintenance management system built with Python and Streamlit. The system allows users to report maintenance issues and uses AI to analyze the reported problem.

The goal of this project is to make maintenance issue reporting easier by automatically categorizing issues, determining their priority, and providing a suggested action.

## Features

- Report maintenance issues
- Store maintenance issues in a database
- Automated issue analysis with Google Gemini
- Automatic issue categorization
- Automatic priority detection
- Generated issue summary
- Suggested maintenance action
- Modern dark SaaS dashboard with sidebar navigation (Dashboard, Issues, Report Issue, Analytics)
- Metric cards, colour-coded priority/status, searchable and filterable issue table
- Search by title, description or location; filter by category, priority, status, department and technician (filters combine)
- Assign technicians and update issue status, with clear success and error messages
- Analytics charts by category, priority, status and department

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
FacilityFlow/
│
├── .streamlit/
│   └── config.toml        # dark theme settings
├── assets/
├── services/
│   ├── ai_service.py      # Gemini analysis (model: gemini-3.5-flash-lite)
│   └── database.py        # Supabase client
├── utils/
│   ├── logic.py           # pure logic: filters, metrics, department mapping, validation
│   ├── repository.py      # reads/updates of the existing `issues` table
│   └── theme.py           # styling and UI components
├── tests/                 # pytest suite (no credentials needed)
├── app.py
├── test_connection.py
├── test_gemini.py
├── requirements.txt
├── .env                   # your credentials (not committed)
├── .gitignore
└── README.md
```

## Setup and Run

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file next to `app.py` containing `SUPABASE_URL`, `SUPABASE_KEY` and `GEMINI_API_KEY` (never commit this file).

3. Start the app:

   ```bash
   streamlit run app.py
   ```

Optional checks: `python test_connection.py` (Supabase) and `python test_gemini.py` (Gemini).

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The main suite uses in-memory stand-ins for Supabase and Gemini, so it needs no `.env`.

`tests/test_integration.py` talks to the real Supabase project and Gemini API. It is skipped
automatically unless `SUPABASE_URL`, `SUPABASE_KEY` and `GEMINI_API_KEY` are available. It only
reads data (and makes one small Gemini request); it never inserts, updates or deletes rows.

## Behaviour notes

- An issue is saved only if the Gemini analysis is complete and valid (category, a priority of
  LOW / MEDIUM / HIGH, summary and suggested action). Otherwise nothing is saved and the error is shown.
- The department is derived from the category when the issue is created. Older rows without a
  department are displayed (and filtered, and charted) using the same mapping; the database is not changed.
- Technicians come from a fixed list in `utils/logic.py`. A technician already stored on an issue
  stays selectable even if it is not in that list.

## Optional extensions (need extra infrastructure, not implemented)

- **Technicians from the database:** requires a new `technicians` table.
- **Department notifications:** requires an external channel (email, Slack, etc.) and its credentials.

