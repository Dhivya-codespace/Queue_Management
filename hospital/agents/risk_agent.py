import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq


# Load variables from .env
load_dotenv()


def risk_agent(state):

    symptoms = state["symptoms"]

    try:

        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY")
        )

        prompt = f"""
You are a preliminary symptom risk assessment assistant
for a hospital queue management system.

Patient symptoms:
{symptoms}

Give a risk score from 0 to 100.

Rules:
80 to 100 = High risk
50 to 79 = Medium risk
0 to 49 = Low risk

Return ONLY the number.
Do not give a diagnosis.
"""

        response = llm.invoke(prompt)

        risk_score = int(response.content.strip())

        if risk_score < 0:
            risk_score = 0

        if risk_score > 100:
            risk_score = 100

    except Exception as e:

        print("LLM Error:", e)

        # Fallback rule-based scoring
        symptoms_lower = symptoms.lower()

        if "chest pain" in symptoms_lower or "breathing difficulty" in symptoms_lower:
            risk_score = 95

        elif "fever" in symptoms_lower or "cough" in symptoms_lower:
            risk_score = 60

        else:
            risk_score = 30

    state["risk_score"] = risk_score

    print("\n===== Groq LLM Risk Assessment Agent =====")
    print("Symptoms :", symptoms)
    print("Risk Score :", risk_score)

    return state