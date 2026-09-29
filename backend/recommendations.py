from .database import get_db

def get_recommendations(user_id):
    db = get_db()
    expense_total = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='expense'", (user_id,)).fetchone()["x"]
    income_total = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='income'", (user_id,)).fetchone()["x"]
    top = db.execute("""SELECT category, SUM(amount) amount FROM transactions
                        WHERE user_id=? AND type='expense'
                        GROUP BY category ORDER BY amount DESC LIMIT 3""",(user_id,)).fetchall()
    recs=[]
    if income_total == 0:
        recs.append("Start with the Budgeting module and add a sample or real income entry so your dashboard can personalize suggestions.")
    elif expense_total > income_total:
        recs.append("Your recorded expenses currently exceed income. Review your largest categories and work through the Budgeting module.")
    elif income_total and expense_total / income_total > .75:
        recs.append("A large share of recorded income is going to expenses. Try the Needs vs Wants project and set a small savings target.")
    else:
        recs.append("Your recorded spending is below income. The Saving and Financial Planning modules can help you turn that gap into goals.")
    if top:
        recs.append(f"Your highest recorded spending category is {top[0]['category']}. Review that category before adding new discretionary spending.")
    goals = db.execute("SELECT COUNT(*) c FROM saving_goals WHERE user_id=?",(user_id,)).fetchone()["c"]
    if goals == 0:
        recs.append("Create your first saving goal to make your progress measurable.")
    return recs
