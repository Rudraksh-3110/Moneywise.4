# MoneyWise

MoneyWise is a local-first financial literacy and personal money-tracking web application.

## Stack

- Python 3.10+
- Flask
- SQLite
- HTML5
- CSS3
- Vanilla JavaScript
- Local SVG effects
- Jinja templates

No Node.js, React, Express, or separate JavaScript backend is required.

## Features

- User registration/login with hashed passwords
- Local SQLite data storage
- Professional dashboard with sponsored-content placeholder
- Virtual wallet
- Income and expense tracking
- Financial summary
- Savings tracking
- Multiple saving goals with progress
- Personalized skill recommendations
- 9 financial skill modules
- Curated external learning sources
- Project-based learning
- Interactive money-literacy quiz
- Money literacy resources
- Offline MoneyWise fallback chatbot
- Explainable, rule-based AI financial insights
- Spending-pattern analysis from the signed-in user's records
- Savings-rate and expense-ratio analysis
- Saving-goal progress and timeline estimates
- AI Insights dashboard
- Responsive desktop/tablet/mobile layout
- SVG visual effects
- JSON-style API endpoint for dashboard summaries

## Run locally

### Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The SQLite database is automatically created at `database/moneywise.db`.

## Important security note

Change `SECRET_KEY` in `app.py` before deploying anywhere public. For production, use HTTPS, environment variables for secrets, CSRF protection, stronger session configuration, rate limiting, and a production WSGI server.

## Data model

Each account's transactions, savings, goals, learning progress, and quiz results are linked to its own user ID. SQLite is local to the installation.

## Curated sources

The starter dataset contains links to established financial education providers. Some sources are jurisdiction-specific. Review local financial/tax rules before applying educational information to real decisions.

## AI system

MoneyWise uses a local, explainable rule-based AI layer rather than an external AI API. The AI combines the signed-in user's income, expenses, savings, spending categories, and saving goals to identify patterns and produce readable insights. The chatbot can also trigger the same analysis when the user asks about patterns or financial analysis.

The AI layer is intentionally additive: it does not modify transactions, savings, goals, login data, or other existing workflows. If the AI layer is unavailable, the normal finance features remain independent. Because the analysis is rule-based, it should be described as explainable/rule-based AI rather than machine learning or generative AI.

It is an educational tool and not a substitute for a qualified financial professional.

## Project structure

```text
MoneyWise/
├── app.py
├── requirements.txt
├── README.md
├── backend/
│   ├── database.py
│   ├── recommendations.py
│   ├── ai_insights.py
│   ├── chatbot.py
│   └── quiz.py
├── database/
│   └── moneywise.db   # created automatically
├── data/
├── static/
│   ├── css/
│   ├── js/
│   └── svg/
└── templates/
```
