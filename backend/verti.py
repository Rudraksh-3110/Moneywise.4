from .database import get_db

SCENARIOS = [
    {
        "id": "insufficient_funds",
        "question": "What if you suddenly face an important expense but do not have sufficient funds? What would you do first?",
        "options": [
            ("review", "Review your budget and available savings before making the decision."),
            ("borrow", "Immediately borrow money without checking the cost."),
            ("ignore", "Ignore the expense and hope the problem disappears."),
            ("impulse", "Spend from money meant for another important goal without checking.")
        ],
        "good": "review",
        "reason": "Checking your budget and available resources first helps you understand the situation before taking a costly action."
    },
    {
        "id": "income_drop",
        "question": "What if your income suddenly drops for a month? What would you do?",
        "options": [
            ("prioritize", "Prioritize essential expenses and temporarily review flexible spending."),
            ("overspend", "Keep spending at the same level and worry about it later."),
            ("goal", "Use all money saved for a long-term goal immediately."),
            ("credit", "Use credit for every expense without checking repayment costs.")
        ],
        "good": "prioritize",
        "reason": "Prioritizing essential expenses gives you a clearer way to manage a temporary income drop."
    },
    {
        "id": "unexpected_purchase",
        "question": "What if you really want something expensive but buying it would leave very little money for the rest of the month?",
        "options": [
            ("wait", "Wait, compare the need with your budget, and decide later."),
            ("buy", "Buy it immediately because you might not get another chance."),
            ("borrow", "Borrow the money just to make the purchase now."),
            ("empty", "Use all your savings without checking your other goals.")
        ],
        "good": "wait",
        "reason": "Pausing lets you compare the purchase with your budget and other financial priorities."
    },
    {
        "id": "goal_pressure",
        "question": "What if a saving goal is getting difficult to reach? What could you do?",
        "options": [
            ("adjust", "Review spending and adjust the plan while keeping the goal realistic."),
            ("quit", "Give up on saving completely."),
            ("hide", "Stop tracking your spending so the problem is less visible."),
            ("risk", "Take a risky shortcut to reach the target faster.")
        ],
        "good": "adjust",
        "reason": "Reviewing the plan can reveal whether spending can be adjusted or the goal timeline needs to change."
    },
    {
        "id": "scam_request",
        "question": "What if someone unexpectedly asks you to share a password or one-time code to solve a money problem?",
        "options": [
            ("verify", "Do not share it and verify the request through an official channel."),
            ("share", "Share it because the person says it is urgent."),
            ("forward", "Forward the code to a friend to decide whether it is safe."),
            ("reply", "Reply with personal details first and ask questions later.")
        ],
        "good": "verify",
        "reason": "Passwords and one-time codes should be protected, and unexpected requests should be verified independently."
    }
]

def get_scenarios():
    return SCENARIOS

def evaluate_scenarios(answers):
    db = get_db()
    income = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='income'", (answers["user_id"],)).fetchone()["x"]
    expenses = db.execute("SELECT COALESCE(SUM(amount),0) x FROM transactions WHERE user_id=? AND type='expense'", (answers["user_id"],)).fetchone()["x"]
    score = 0
    results = []

    for scenario in SCENARIOS:
        choice = answers.get(scenario["id"])
        correct = choice == scenario["good"]
        if correct:
            score += 1
        selected_text = next((label for value, label in scenario["options"] if value == choice), "No response")
        results.append({
            "question": scenario["question"],
            "selected": selected_text,
            "correct": correct,
            "reason": scenario["reason"]
        })

    if score == len(SCENARIOS):
        summary = "Your decisions consistently show careful budgeting, planning and financial safety."
    elif score >= 3:
        summary = "Your decisions show several strong money-management habits. Review the situations where you chose a different approach."
    else:
        summary = "These situations highlight areas where planning, budgeting and financial safety can be strengthened."

    if income > expenses:
        summary += " Your recorded dashboard also shows income above recorded expenses."
    elif income < expenses:
        summary += " Your recorded expenses are currently above recorded income, so reviewing your budget may be especially useful."
    else:
        summary += " Your recorded income and expenses are currently at the same level."

    return {"score": score, "total": len(SCENARIOS), "summary": summary, "results": results}
