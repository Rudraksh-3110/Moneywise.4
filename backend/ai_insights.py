from datetime import datetime
from .database import get_db


def _money(value):
    return f"₹{value:,.0f}"


def get_ai_insights(user_id):
    """Local, explainable financial analysis for the MoneyWise AI layer."""
    db = get_db()
    income = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='income'", (user_id,)).fetchone()["x"]
    expenses = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='expense'", (user_id,)).fetchone()["x"]
    saved = db.execute("SELECT COALESCE(SUM(amount),0) x FROM savings WHERE user_id=?", (user_id,)).fetchone()["x"]
    categories = db.execute("""SELECT category, SUM(amount) amount FROM transactions
        WHERE user_id=? AND type='expense' GROUP BY category ORDER BY amount DESC""", (user_id,)).fetchall()
    goals = db.execute("SELECT name,target_amount,current_amount,deadline FROM saving_goals WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()

    balance = income - expenses - saved
    expense_ratio = (expenses / income * 100) if income else 0
    savings_ratio = (saved / income * 100) if income else 0
    insights = []

    if income == 0 and expenses == 0:
        insights.append({"type": "starter", "title": "Start with your data", "text": "Add income and expense entries so MoneyWise AI can identify patterns from your own records."})
    elif expenses > income:
        insights.append({"type": "attention", "title": "Expenses are above income", "text": f"Recorded expenses are {_money(expenses-income)} higher than recorded income. Review your largest categories before increasing discretionary spending."})
    elif expense_ratio >= 75:
        insights.append({"type": "attention", "title": "High spending share", "text": f"About {expense_ratio:.0f}% of recorded income is currently represented by expenses. A budget review could create more room for goals."})
    else:
        insights.append({"type": "positive", "title": "Room for goals", "text": f"Recorded expenses use about {expense_ratio:.0f}% of income, leaving approximately {_money(income-expenses)} before savings are counted."})

    if saved > 0 and income > 0:
        insights.append({"type": "saving", "title": "Savings rate", "text": f"Your recorded savings are about {savings_ratio:.0f}% of recorded income. Keep tracking contributions to see how the rate changes over time."})
    elif income > 0:
        insights.append({"type": "saving", "title": "Build a saving habit", "text": "No savings are recorded yet. Consider setting a small, specific goal and recording each contribution."})

    if categories:
        top = categories[0]
        share = (top["amount"] / expenses * 100) if expenses else 0
        insights.append({"type": "pattern", "title": f"Top spending category: {top['category']}", "text": f"{top['category']} represents about {share:.0f}% of recorded expenses ({_money(top['amount'])}). This is a useful category to review when planning your next budget."})

    goal_cards = []
    today = datetime.now().date()
    earliest_saving = db.execute("SELECT MIN(created_at) first_date FROM savings WHERE user_id=?", (user_id,)).fetchone()["first_date"]
    if earliest_saving and saved > 0:
        try:
            first_date = datetime.fromisoformat(earliest_saving).date()
            months_elapsed = max(1, (today.year - first_date.year) * 12 + today.month - first_date.month + 1)
            monthly_saving_rate = saved / months_elapsed
        except ValueError:
            monthly_saving_rate = saved
    else:
        monthly_saving_rate = 0
    for goal in goals[:5]:
        remaining = max(goal["target_amount"] - goal["current_amount"], 0)
        pct = min((goal["current_amount"] / goal["target_amount"] * 100) if goal["target_amount"] else 0, 100)
        months = max(1, round(remaining / monthly_saving_rate)) if remaining > 0 and monthly_saving_rate > 0 else None
        deadline_note = ""
        if goal["deadline"]:
            try:
                deadline = datetime.fromisoformat(goal["deadline"]).date()
                days = (deadline - today).days
                deadline_note = f" Deadline is in {max(days, 0)} days." if days >= 0 else " The recorded deadline has passed."
            except ValueError:
                pass
        estimate = f" At the current total savings rate, the remaining amount is roughly {months} month(s) away based on your recorded saving pace." if months else ""
        goal_cards.append({"name": goal["name"], "percent": round(pct), "remaining": remaining, "note": deadline_note + estimate})

    if not goals:
        insights.append({"type": "goal", "title": "No saving goal yet", "text": "Create a goal with a target and deadline so MoneyWise can track progress and estimate the remaining amount."})

    return {
        "metrics": {"income": income, "expenses": expenses, "saved": saved, "balance": balance,
                    "expense_ratio": round(expense_ratio, 1), "savings_ratio": round(savings_ratio, 1)},
        "insights": insights[:5],
        "goals": goal_cards,
        "categories": [{"category": r["category"], "amount": r["amount"]} for r in categories[:5]],
    }
