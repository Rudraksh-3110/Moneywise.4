def analyze_what_if(income, expenses, saved, monthly_change, mode):
    """
    Explainable, rule-based AI-style what-if analysis.
    This is a hypothetical calculation only; it never changes user records.
    """
    income = float(income or 0)
    expenses = float(expenses or 0)
    saved = float(saved or 0)
    monthly_change = max(0.0, float(monthly_change or 0))

    current_monthly_surplus = income - expenses

    if mode == "save_more":
        new_monthly_surplus = current_monthly_surplus + monthly_change
        action = f"save ₹{monthly_change:,.2f} more each month"
    else:
        new_monthly_surplus = current_monthly_surplus + monthly_change
        action = f"reduce expenses by ₹{monthly_change:,.2f} each month"

    six_month_change = monthly_change * 6
    twelve_month_change = monthly_change * 12

    if new_monthly_surplus > 0:
        months_to_extra_10000 = 10000 / new_monthly_surplus
        outlook = "Your projected monthly surplus stays positive under this scenario."
    elif new_monthly_surplus == 0:
        months_to_extra_10000 = None
        outlook = "This scenario brings the projected monthly surplus to zero."
    else:
        months_to_extra_10000 = None
        outlook = "This scenario still leaves a projected monthly shortfall."

    if monthly_change == 0:
        insight = "Enter a change above ₹0 to see how the scenario affects your projection."
    elif mode == "reduce_expenses":
        insight = f"Reducing expenses by ₹{monthly_change:,.2f} could free ₹{six_month_change:,.2f} over 6 months and ₹{twelve_month_change:,.2f} over 12 months."
    else:
        insight = f"Saving an extra ₹{monthly_change:,.2f} each month could add ₹{six_month_change:,.2f} to savings over 6 months and ₹{twelve_month_change:,.2f} over 12 months."

    change_share = (monthly_change / income) * 100 if income > 0 else 0

    if change_share >= 25:
        difficulty = "Large change"
        difficulty_note = "This is a substantial change compared with your recorded income, so try a smaller scenario too."
    elif change_share >= 10:
        difficulty = "Moderate change"
        difficulty_note = "This is a noticeable change compared with your recorded income."
    else:
        difficulty = "Small change"
        difficulty_note = "This is a relatively small change compared with your recorded income."

    return {
        "mode": mode,
        "monthly_change": monthly_change,
        "current_surplus": current_monthly_surplus,
        "new_surplus": new_monthly_surplus,
        "six_month_change": six_month_change,
        "twelve_month_change": twelve_month_change,
        "months_to_extra_10000": months_to_extra_10000,
        "outlook": outlook,
        "insight": insight,
        "action": action,
        "difficulty": difficulty,
        "difficulty_note": difficulty_note,
        "recorded_saved": saved,
        "recorded_income": income,
        "recorded_expenses": expenses,
    }
