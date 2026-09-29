---
title: FitBuddy
emoji: 💪
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
short_description: AI fitness plan generator with FastAPI and Gemini
---

# FitBuddy – AI Fitness Plan Generator

FitBuddy is an AI-powered fitness planning web app built with FastAPI,
Jinja2, SQLite + SQLAlchemy, Pydantic, and Google Gemini.

## Features

1. **Personalized workout generation** – enter name, user ID, age, weight,
   goal and intensity to get a structured 7-day plan (shown as day cards).
2. **Nutrition & recovery tip** – a short, general tip for your goal.
3. **Feedback-based updates** – e.g. "add more cardio" or "add a rest day";
   the updated plan is stored separately from the original.
4. **SQLite storage** – user profiles and all plan versions are saved.
5. **Admin dashboard** – `/view-all-users` shows every user, their original
   and updated plans, and their feedback, with a delete option.
6. **JSON API** – documented automatically at `/docs`.

| Method | Endpoint        | Description                          |
|--------|-----------------|--------------------------------------|
| GET    | `/api/health`   | Health check (shows demo/gemini mode)|
| POST   | `/api/workout`  | Create a user + 7-day plan           |
| POST   | `/api/feedback` | Update a user's plan from feedback   |
| GET    | `/api/users`    | List users (needs `X-Admin-Key` if set) |

## Setup

### 1. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activate script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your `.env`

Copy `.env.example` to `.env`. Leave `GEMINI_API_KEY` blank to use demo
mode, or add your key:

```
GEMINI_API_KEY=your_actual_api_key
```

Never put the API key directly in Python files.

### 4. Run the app

```bash
uvicorn app.main:app --reload
```

Then open:

- App: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Dashboard: http://127.0.0.1:8000/view-all-users

## Demo mode

With no Gemini key, FitBuddy returns a built-in sample plan, so you can test
the forms, database, feedback flow, dashboard and API without any API costs.
`/api/health` reports `"mode": "demo"` or `"mode": "gemini"`.

## Tests

```bash
pytest -q
```

Expected: `9 passed`. Tests always run in demo mode and use a separate
`test_fitbuddy.db`, so they never call Gemini or touch your real data.

## Project structure

```
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── config.py                 # settings from .env
│   ├── database.py               # SQLAlchemy models + helpers
│   ├── schemas.py                # Pydantic input/output schemas
│   ├── ai_client.py              # shared Gemini call + error handling
│   ├── gemini_generator.py       # 7-day workout plan
│   ├── gemini_flash_generator.py # nutrition/recovery tip
│   ├── updated_plan.py           # feedback-based plan update
│   ├── routes.py                 # web pages + API
│   └── main.py                   # FastAPI app
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── admin_login.html
│   └── all_users.html
├── static/css/styles.css
├── tests/
│   ├── conftest.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Known limitations

- There is no user login: anyone who knows a user ID can overwrite that
  profile or submit feedback for it. Fine for a demo; add authentication
  before real use.
- The admin key is passed in the URL. Set `ADMIN_KEY` before deploying, and
  consider session-based admin login for production.

## Important

FitBuddy is an educational wellness application. AI-generated information is
not medical diagnosis or treatment. Anyone with an injury, medical condition,
severe pain or other health concern should consult a qualified professional.
