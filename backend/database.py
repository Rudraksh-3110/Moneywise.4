import sqlite3, os, json
from pathlib import Path
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 email TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 type TEXT NOT NULL CHECK(type IN ('income','expense')),
 amount REAL NOT NULL,
 category TEXT NOT NULL,
 note TEXT DEFAULT '',
 created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS savings(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 amount REAL NOT NULL,
 note TEXT DEFAULT '',
 created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS saving_goals(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 name TEXT NOT NULL,
 target_amount REAL NOT NULL,
 current_amount REAL NOT NULL DEFAULT 0,
 deadline TEXT,
 created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS skills(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 level TEXT NOT NULL,
 icon TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_sources(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 skill_id INTEGER,
 title TEXT NOT NULL,
 provider TEXT NOT NULL,
 url TEXT NOT NULL,
 description TEXT NOT NULL,
 FOREIGN KEY(skill_id) REFERENCES skills(id)
);
CREATE TABLE IF NOT EXISTS projects(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 skill_id INTEGER,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 steps TEXT NOT NULL,
 FOREIGN KEY(skill_id) REFERENCES skills(id)
);
CREATE TABLE IF NOT EXISTS user_skill_progress(
 user_id INTEGER NOT NULL,
 skill_id INTEGER NOT NULL,
 completed INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY(user_id,skill_id),
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS quiz_results(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 score INTEGER NOT NULL,
 total INTEGER NOT NULL,
 created_at TEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

def get_db():
    if "db" not in g:
        db_path = current_app.config.get("DATABASE", "database/moneywise.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db_path = current_app.config.get("DATABASE", "database/moneywise.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    db.commit()
    db.close()
    current_app.teardown_appcontext(close_db)

def seed_db():
    db = get_db()
    skills = [
        ("Budgeting","Build a realistic plan for where your money goes.","Beginner","◫"),
        ("Saving","Learn how to create saving habits and emergency buffers.","Beginner","◇"),
        ("Needs vs Wants","Make thoughtful spending decisions using simple frameworks.","Beginner","◆"),
        ("Banking Basics","Understand accounts, transfers, interest and common fees.","Beginner","▣"),
        ("Investing Basics","Learn the foundational concepts behind long-term investing.","Intermediate","↗"),
        ("Credit & Debt","Understand borrowing, interest, repayments and credit history.","Intermediate","◉"),
        ("Taxes","Learn the basics of income, deductions and responsible record keeping.","Intermediate","▤"),
        ("Financial Safety","Recognize scams, protect accounts and practice digital safety.","Beginner","✓"),
        ("Financial Planning","Turn goals into a practical longer-term money plan.","Intermediate","⌁")
    ]
    existing = db.execute("SELECT title FROM skills ORDER BY id").fetchall()
    titles = [r["title"] for r in existing]
    target_titles = [s[0] for s in skills]

    # Restore the original financial-literacy learning catalog if the
    # database currently contains the newer learn-and-earn catalog.
    if titles != target_titles:
        db.execute("DELETE FROM learning_sources")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM user_skill_progress")
        db.execute("DELETE FROM skills")
        db.commit()

    if db.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"] == 0:
        db.executemany("INSERT INTO skills(title,description,level,icon) VALUES(?,?,?,?)", skills)
    sources = [
        (1,"Budgeting basics","Consumer Financial Protection Bureau","https://www.consumerfinance.gov/consumer-tools/budgeting/","Practical budgeting education and tools."),
        (2,"Saving money","Consumer Financial Protection Bureau","https://www.consumerfinance.gov/consumer-tools/saving/","Educational guidance about saving and goals."),
        (3,"Needs vs wants","Consumer Financial Protection Bureau","https://www.consumerfinance.gov/consumer-tools/","Explore consumer money-management resources."),
        (4,"Money and banking","FDIC Money Smart","https://www.fdic.gov/resources/consumers/money-smart/","Financial education resources from the FDIC."),
        (5,"Investor education","Investor.gov","https://www.investor.gov/","SEC investor education and foundational concepts."),
        (6,"Credit and loans","Consumer Financial Protection Bureau","https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/","Learn about credit reports and scores."),
        (7,"Tax education","IRS Tax Information","https://www.irs.gov/individuals","Official U.S. tax information; use local tax authority guidance for your jurisdiction."),
        (8,"Online safety","FTC Consumer Advice","https://consumer.ftc.gov/","Consumer and scam-awareness resources."),
        (9,"Financial education","Khan Academy","https://www.khanacademy.org/college-careers-more/personal-finance","Free personal-finance learning materials.")
    ]
    db.executemany("INSERT INTO learning_sources(skill_id,title,provider,url,description) VALUES(?,?,?,?,?)", sources)
    projects = [
        (1,"Build a 30-day budget","Create a month-long budget from your real income and typical expenses.","List income|List fixed expenses|Estimate flexible expenses|Set a savings target|Review at month end"),
        (2,"Savings challenge","Create a small, achievable savings target and track it for four weeks.","Choose a goal|Set weekly targets|Log contributions|Review progress"),
        (3,"Needs or wants audit","Review ten recent purchases and classify the reason behind each one.","Pick ten purchases|Label needs or wants|Write one alternative for each want|Choose one spending change"),
        (4,"Bank account comparison","Compare two account types using fees, access and features.","Choose two accounts|Record fees|Compare access|Summarize trade-offs"),
        (5,"Investment vocabulary map","Create a one-page map of basic investing terms.","Define diversification|Define risk|Define return|Define fees|Explain compounding"),
        (6,"Debt payoff simulation","Use a spreadsheet or paper to model how repayment amounts change total interest.","Choose a fictional balance|Choose an interest rate|Compare repayment amounts|Record observations"),
        (7,"Tax document checklist","Build a personal checklist of documents to keep for tax time.","Identify income records|Identify deductible records|Create a secure storage plan|Review annually"),
        (8,"Scam spotting drill","Collect examples of common scam warning signs from trusted sources.","Read safety guidance|List red flags|Create a verification checklist|Teach someone else"),
        (9,"One-year money plan","Create a one-page plan for savings, spending and learning goals.","Choose three goals|Assign target dates|Estimate monthly actions|Review quarterly")
    ]
    db.executemany("INSERT INTO projects(skill_id,title,description,steps) VALUES(?,?,?,?)", projects)
    db.commit()
