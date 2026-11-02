# Agentic AI-Based Hospital Queue Management System

## About the Project

The Agentic AI-Based Hospital Queue Management System is a web-based healthcare platform designed to simplify hospital appointment scheduling and patient queue management.

The system uses multiple AI agents to assist with symptom analysis, risk assessment, doctor recommendations, appointment booking, and queue management.

## Key Features

- Patient and doctor login
- Patient symptom submission and analysis
- AI-based risk assessment
- Doctor recommendation
- Appointment booking and management
- Automatic token generation
- Patient queue position tracking
- Appointment history
- Doctor dashboard
- Location tracking
- Patient feedback management

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Django |
| Database | SQLite |
| ORM | Django ORM |
| AI Agents | Python |
| AI API | Grok API (xAI) |
| Maps | Leaflet.js, OpenStreetMap |
| Version Control | Git, GitHub |
| CI/CD | GitHub Actions (planned) |

## Project Structure

```text
Queue_Management/
│
├── config/
├── hospital/
│   ├── agents/
│   ├── migrations/
│   ├── static/
│   └── templates/
│
├── ml/
├── manage.py
├── test_agents.py
├── fix_views.py
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Dhivya-codespace/Queue_Management.git
```

### 2. Navigate to the project folder

```bash
cd Queue_Management
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the environment (Windows)

```bash
.venv\Scripts\activate
```

### 5. Install dependencies

If a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

### 6. Apply migrations

```bash
python manage.py migrate
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Future Enhancements

- Automated SMS and email notifications
- Predictive hospital queue analysis
- Mobile application integration
- Improved multilingual support
- Automated deployment using CI/CD

## Project Status

The project is under development. Additional testing and CI/CD integration are planned.

## Author

**Dhivya-codespace**

GitHub: https://github.com/Dhivya-codespace

