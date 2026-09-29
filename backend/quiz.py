QUESTIONS = [
 {"id":1,"q":"What is a budget mainly used for?","options":["To guarantee profit","To plan income and spending","To eliminate all expenses","To predict stock prices"],"answer":"To plan income and spending","why":"A budget is a plan for allocating expected income across spending, saving and other priorities."},
 {"id":2,"q":"Which is generally an example of an emergency fund purpose?","options":["Buying collectibles","Handling an unexpected necessary expense","Increasing impulse purchases","Avoiding all banking"],"answer":"Handling an unexpected necessary expense","why":"Emergency savings can help cover unexpected necessary costs."},
 {"id":3,"q":"What does diversification mean in investing?","options":["Putting everything in one asset","Spreading investments across different assets","Only buying cash","Avoiding all risk"],"answer":"Spreading investments across different assets","why":"Diversification spreads exposure rather than concentrating it."},
 {"id":4,"q":"What is interest?","options":["A type of password","A cost or return associated with borrowing or saving money","A spending category","A tax form"],"answer":"A cost or return associated with borrowing or saving money","why":"Interest can be paid by a borrower or earned by a saver/investor depending on the product."},
 {"id":5,"q":"Which action improves account security?","options":["Sharing an OTP","Reusing one password everywhere","Using unique strong passwords","Posting account details publicly"],"answer":"Using unique strong passwords","why":"Unique strong passwords reduce the impact of a compromised credential."},
 {"id":6,"q":"What is a financial goal?","options":["A measurable money objective","A random purchase","A bank password","A tax penalty"],"answer":"A measurable money objective","why":"Goals give savings and spending decisions a defined purpose."}
]
def get_quiz(): return QUESTIONS
def grade_quiz(answers):
    score=0; details=[]
    for q in QUESTIONS:
        chosen=answers.get(q["id"],"")
        ok=chosen==q["answer"]
        score += int(ok)
        details.append({"q":q["q"],"chosen":chosen or "No answer","correct":q["answer"],"ok":ok,"why":q["why"]})
    return {"score":score,"total":len(QUESTIONS),"percent":round(score/len(QUESTIONS)*100),"details":details}
