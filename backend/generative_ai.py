"""Optional Generative AI service for MoneyWise.

The feature is deliberately isolated from the normal finance system. If the
API key is missing, the provider is unavailable, or a request fails, callers
receive a safe fallback message instead of an application error.
"""

import json
import os
from urllib import error, request


API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")


def _fallback(message):
    return (
        "Generative AI is currently unavailable. "
        "MoneyWise's built-in rule-based assistant is still available. "
        "Try asking about your balance, spending, saving, budgeting, or "
        "financial safety."
    )


def generate_moneywise_response(message, financial_context):
    """Generate an educational response, or safely fall back.

    Only aggregate financial figures are sent to the model; account names,
    email addresses, passwords, and transaction notes are not included.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or not message.strip():
        return _fallback(message)

    income = float(financial_context.get("income", 0) or 0)
    expenses = float(financial_context.get("expenses", 0) or 0)
    saved = float(financial_context.get("saved", 0) or 0)
    balance = float(financial_context.get("balance", 0) or 0)
    expense_ratio = (expenses / income * 100) if income > 0 else 0
    savings_ratio = (saved / income * 100) if income > 0 else 0

    categories = financial_context.get("categories", [])
    category_text = ", ".join(
        f"{row['category']}: ₹{float(row['amount']):.2f}" for row in categories[:5]
    ) or "No expense categories recorded."

    prompt = f"""
You are MoneyWise Generative AI, an educational financial-literacy assistant
for students. Give clear, age-appropriate educational explanations. Do not
give instructions to buy or sell financial products, make investments, take
loans, or make other high-stakes financial decisions. Do not pretend to be a
financial professional. Encourage checking official/local sources for laws,
taxes, and financial products.

The user's MoneyWise data is:
- Recorded income: ₹{income:.2f}
- Recorded expenses: ₹{expenses:.2f}
- Recorded savings: ₹{saved:.2f}
- Recorded balance: ₹{balance:.2f}
- Expense share of income: {expense_ratio:.1f}%
- Savings share of income: {savings_ratio:.1f}%
- Top recorded expense categories: {category_text}

Answer the user's question using the data only when it is relevant. Clearly
say when there is not enough recorded data. Never invent transactions or
personal information.

User question:
{message.strip()}
""".strip()

    payload = json.dumps({
        "model": DEFAULT_MODEL,
        "input": prompt,
        "max_output_tokens": 500
    }).encode("utf-8")

    req = request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        # Defensive parser for responses where output_text is not returned.
        parts = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if isinstance(text, str):
                    parts.append(text)
        result = "\n".join(parts).strip()
        return result if result else _fallback(message)

    except (error.HTTPError, error.URLError, TimeoutError, ValueError, OSError):
        return _fallback(message)
