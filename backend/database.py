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
CREATE TABLE IF NOT EXISTS learning_topics(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 level TEXT NOT NULL,
 icon TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_content_sources(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 topic_id INTEGER NOT NULL,
 title TEXT NOT NULL,
 provider TEXT NOT NULL,
 url TEXT NOT NULL,
 description TEXT NOT NULL,
 FOREIGN KEY(topic_id) REFERENCES learning_topics(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS learning_projects(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 topic_id INTEGER NOT NULL,
 title TEXT NOT NULL,
 description TEXT NOT NULL,
 steps TEXT NOT NULL,
 FOREIGN KEY(topic_id) REFERENCES learning_topics(id) ON DELETE CASCADE
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

    # Skills are career / earn-and-learn skills and are independent from
    # the financial-literacy Learning section.
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
    target_titles = [s[0] for s in skills]

    if titles != target_titles:
        db.execute("DELETE FROM learning_sources")
        db.execute("DELETE FROM projects")
        db.execute("DELETE FROM user_skill_progress")
        db.execute("DELETE FROM skills")
        db.commit()

    if db.execute("SELECT COUNT(*) c FROM skills").fetchone()["c"] == 0:
        db.executemany("INSERT INTO skills(title,description,level,icon) VALUES(?,?,?,?)", skills)

    career_sources = [
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
    career_projects = [
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
    db.execute("DELETE FROM learning_sources")
    db.execute("DELETE FROM projects")
    db.executemany("INSERT INTO learning_sources(skill_id,title,provider,url,description) VALUES(?,?,?,?,?)", career_sources)
    db.executemany("INSERT INTO projects(skill_id,title,description,steps) VALUES(?,?,?,?)", career_projects)

    # Financial literacy belongs to Learning, not Skills.
    topics = [
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
    db.execute("DELETE FROM learning_content_sources")
    db.execute("DELETE FROM learning_projects")
    db.execute("DELETE FROM learning_topics")
    db.executemany("INSERT INTO learning_topics(title,description,level,icon) VALUES(?,?,?,?)", topics)
    sources = [
        (1,"Budgeting basics","Reserve Bank of India (RBI)","https://www.rbi.org.in/FinancialEducation/content/I%20Can%20Do_RBI.pdf","RBI financial education resource covering budgeting and practical money management."),
        (2,"Budgeting, Saving and Responsible Borrowing","Reserve Bank of India (RBI)","https://www.rbi.org.in/commonman/images/FAME%20Booklet%20second%20edition/FAME%20Booklet%20English/FAME30072020.pdf","RBI financial awareness material covering saving, budgeting and responsible borrowing."),
        (3,"Financial Literacy for School Children","Reserve Bank of India (RBI)","https://www.rbi.org.in/commonman/English/content/01SCHOOL20042018.pdf","RBI educational material designed to introduce school students to financial concepts."),
        (4,"Financial Literacy for School Children","Reserve Bank of India (RBI)","https://www.rbi.org.in/commonman/English/content/01SCHOOL20042018.pdf","RBI material covering banking basics, accounts and common banking services."),
        (5,"Financial Education Booklet","SEBI Investor Education","https://investor.sebi.gov.in/pdf/downloadable-documents/Financial%20Education%20Booklet%20-%20English.pdf","SEBI educational material covering saving, investing, risk, debt and financial concepts."),
        (6,"Financial Education Booklet","SEBI Investor Education","https://investor.sebi.gov.in/pdf/downloadable-documents/Financial%20Education%20Booklet%20-%20English.pdf","SEBI educational material explaining debt and related financial concepts."),
        (7,"Learn with Us — Individual Taxpayer","Income Tax Department, Government of India","https://www.incometax.gov.in/iec/foportal/help/all-topics/tax-payer/individual","Official Indian income-tax guidance for individual taxpayers."),
        (8,"Cyber Safety and Financial Fraud","Indian Cybercrime Coordination Centre (I4C), Ministry of Home Affairs","https://www.cybercrime.gov.in/","Government of India cyber-safety resources, including financial-fraud awareness and reporting."),
        (9,"Financial Education Booklet","SEBI Investor Education","https://investor.sebi.gov.in/pdf/downloadable-documents/Financial%20Education%20Booklet%20-%20English.pdf","SEBI financial-education material covering financial planning, saving, investing and related concepts.")
    ]
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
    db.executemany("INSERT INTO learning_content_sources(topic_id,title,provider,url,description) VALUES(?,?,?,?,?)", sources)
    db.executemany("INSERT INTO learning_projects(topic_id,title,description,steps) VALUES(?,?,?,?)", projects)
    db.commit()
