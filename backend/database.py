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
        ("Python Programming","Learn Python fundamentals and build useful small programs, scripts and automation tools.","Beginner","<>"),
        ("Graphic Design","Learn visual design, layouts, branding and digital graphics that can become freelance work.","Beginner","✦"),
        ("Video Editing","Learn to edit short videos, reels and presentations for creators, businesses and school projects.","Beginner","▶"),
        ("Web Development","Learn HTML, CSS, JavaScript and the basics of building websites and web applications.","Intermediate","</>"),
        ("UI/UX Design","Learn how to design clear interfaces, user flows, wireframes and prototypes.","Intermediate","▣"),
        ("Content Creation","Learn writing, storytelling, presentation and social-media content skills.","Beginner","✎"),
        ("Digital Marketing","Learn social media, search, basic analytics and online promotion for projects and small businesses.","Intermediate","↗"),
        ("Data Analysis","Learn spreadsheets, data cleaning, charts and basic analysis to turn data into useful insights.","Intermediate","▥"),
        ("AI & Automation","Learn practical AI concepts, prompt design and simple automation workflows for modern work.","Intermediate","⌁")
    ]

    existing = db.execute("SELECT title FROM skills ORDER BY id").fetchall()
    titles = [r["title"] for r in existing]

    # Migrate the original financial-literacy skill catalog to the new
    # learn-and-earn career skills without touching user financial data.
    if titles != [s[0] for s in skills]:
        db.execute("DELETE FROM learning_sources")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM user_skill_progress")
        db.execute("DELETE FROM skills")
        db.executemany("INSERT INTO skills(title,description,level,icon) VALUES(?,?,?,?)", skills)

    sources = [
        (1,"Python Tutorial","Python.org","https://docs.python.org/3/tutorial/","Official Python tutorial for learning the language."),
        (2,"Design School","Canva","https://www.canva.com/designschool/","Design lessons and practical visual-design resources."),
        (3,"Video editing learning","Adobe","https://helpx.adobe.com/premiere-pro/tutorials.html","Tutorials for learning professional video-editing concepts."),
        (4,"Learn Web Development","freeCodeCamp","https://www.freecodecamp.org/learn/","Free interactive courses for web development."),
        (5,"Figma Learn","Figma","https://help.figma.com/hc/en-us/categories/360002051613-Learn-design","Resources for learning interface design and prototyping."),
        (6,"Content Marketing Education","HubSpot Academy","https://academy.hubspot.com/","Free courses covering content and digital communication."),
        (7,"Digital Marketing Courses","Google Skillshop","https://skillshop.withgoogle.com/","Training for digital marketing and Google tools."),
        (8,"Learn Data Skills","Kaggle","https://www.kaggle.com/learn","Practical lessons for data analysis and related skills."),
        (9,"AI learning resources","Microsoft Learn","https://learn.microsoft.com/training/","Learning paths covering AI, automation and modern technology.")
    ]

    projects = [
        (1,"Build a Python Utility","Create a small Python program that solves a real student problem.","Choose a problem|Plan the logic|Build the program|Test it|Improve the interface"),
        (2,"Design a Brand Kit","Create a simple visual identity for a fictional student business.","Choose a business idea|Create a logo concept|Choose typography|Create social graphics|Present the brand kit"),
        (3,"Edit a Short Video","Create a polished 30–60 second video for a school project or fictional client.","Choose footage|Create a storyboard|Edit clips|Add text and audio|Export and review"),
        (4,"Build a Portfolio Website","Create a responsive personal portfolio website.","Plan sections|Write HTML|Style with CSS|Add JavaScript|Publish and test"),
        (5,"Design a Mobile App","Create a clickable prototype for a useful student app.","Identify the user|Sketch screens|Create wireframes|Build a prototype|Test the flow"),
        (6,"Create a Content Pack","Create a week of useful content for a fictional creator or small business.","Choose a niche|Plan topics|Write posts|Create visuals|Prepare a posting schedule"),
        (7,"Create a Marketing Campaign","Plan a simple digital campaign for a fictional student business.","Define audience|Set a goal|Create content ideas|Choose channels|Measure results"),
        (8,"Analyze a Dataset","Turn a small public dataset into useful charts and conclusions.","Find data|Clean it|Calculate key values|Create charts|Explain the findings"),
        (9,"Build an AI Workflow","Design a simple workflow that uses AI responsibly to reduce repetitive work.","Choose a task|Define inputs|Create prompts|Design the workflow|Test and document it")
    ]

    # Keep the catalog correct even when an existing database already contains
    # the older seed data. This does not modify financial/account records.
    if db.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"] == 0:
        db.executemany("INSERT INTO skills(title,description,level,icon) VALUES(?,?,?,?)", skills)

    db.execute("DELETE FROM learning_sources")
    db.execute("DELETE FROM projects")
    db.executemany("INSERT INTO learning_sources(skill_id,title,provider,url,description) VALUES(?,?,?,?,?)", sources)
    db.executemany("INSERT INTO projects(skill_id,title,description,steps) VALUES(?,?,?,?)", projects)
    db.commit()
