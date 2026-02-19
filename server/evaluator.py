import os
from openai import OpenAI
from services.assistant import ask_policy

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

test_cases = [
    {
        "question": "What is the emergency dental limit for TravelEase?",
        "expected": "$300 for pain relief and $3,000 for accidental dental"
    },
    {
        "question": "Which all-inclusive plan can a 77 year old buy for 45 days?",
        "expected": "All-Inclusive plan with 45 day limit for age 75+"
    },
    {
        "question": "Which plans cover hospital allowance?",
        "expected": (
            "MUST contain ALL of these: "
            "1. Emergency Medical covered at $50/day up to $500. "
            "2. All-Inclusive covered at $50/day up to $500. "
            "3. Youth All-Inclusive covered at $50/day up to $500. "
            "4. Youth Deluxe All-Inclusive covered at $50/day up to $500. "
            "5. Multi-Trip Emergency Medical covered at $50/day up to $500. "
            "6. Multi-Trip All-Inclusive covered at $50/day up to $500. "
            "7. TravelEase plans NOT covered. "
        )
    },
    {
        "question": "How do I file a claim?",
        "expected": "Information not available in the document"
    }
]

def judge_answer(question, actual_answer, expected_answer):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
           messages=[{
                "role": "system",
                "content": (
                    "You are a strict evaluator. "
                    "You will be given a question, expected information, and an actual answer. "
                    "Check if ALL expected information appears in the actual answer. "
                    "Extra correct information is NOT a reason to fail. "
                    "Reply with PASS or FAIL followed by one sentence explaining why. "
                    "Never ask for more information — always give a verdict."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Expected information: {expected_answer}\n"
                    f"Actual answer: {actual_answer}\n\n"
                    f"Give your verdict now."
                )
            }],
        temperature=0
    )
    return response.choices[0].message.content.strip()


def run_evals():
    print("Running evaluations...\n")
    passed = 0

    for i, test in enumerate(test_cases):
        print(f"\nTEST CASE {i+1}")

        print(f"Question: {test['question']}")

        actual_answer = ask_policy(test["question"])
        print(f"Actual Answer: {actual_answer}")

        evaluation = judge_answer(test["question"], actual_answer, test["expected"])
        print(f"Evaluation: {evaluation}")

        status =  "PASS" if evaluation.startswith("PASS") else "FAIL"
        print(f"{status} Test {i+1}: {test['question']}")
        print(f"   Verdict: {evaluation}")
        print()

        if evaluation.startswith("PASS"):
            passed += 1
        
        print(f"Final Score: {passed}/{len(test_cases)}  = {(passed/len(test_cases))*100:.2f}% accuracy")








if __name__ == "__main__":
    run_evals()



