from .database import get_db

def answer(message, user_id):
    m = message.lower().strip()
    db = get_db()
    income = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='income'",(user_id,)).fetchone()["x"]
    expense = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='expense'",(user_id,)).fetchone()["x"]
    saved = db.execute("SELECT COALESCE(SUM(amount),0) x FROM savings WHERE user_id=?",(user_id,)).fetchone()["x"]

    if any(w in m for w in ["balance","left","wallet"]):
        return f"Your recorded balance is ₹{income-expense-saved:,.2f}. This is based only on entries you have added to MoneyWise."
    if "spend" in m or "expense" in m:
        return f"You have recorded ₹{expense:,.2f} in expenses. Check the Expenses page to see categories and identify areas to review."
    if "save" in m or "saving" in m:
        return f"You have recorded ₹{saved:,.2f} in savings. Try creating a specific saving goal with a target and deadline."
    if "budget" in m:
        return "A simple budget starts with income, fixed essentials, flexible spending and a savings target. Use the Budgeting skill and 30-day project in MoneyWise."
    if "invest" in m:
        return "For learning purposes, start with diversification, risk, return, fees and time horizon. MoneyWise links to Investor.gov for foundational investor education."
    if "debt" in m or "credit" in m:
        return "Learn the difference between principal, interest, fees, minimum payments and repayment schedules. The Credit & Debt module is a good starting point."
    if "scam" in m or "safe" in m:
        return "Do not share passwords or one-time codes. Verify unexpected requests using an official channel, and learn more in the Financial Safety module."
    return "I’m MoneyWise’s offline fallback assistant. I can explain budgeting, saving, spending, credit, investing basics, financial safety and your recorded dashboard numbers. Try asking about your balance, spending, saving, or a money skill."
