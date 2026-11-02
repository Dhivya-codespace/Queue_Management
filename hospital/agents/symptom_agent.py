# agents/symptom_agent.py

class SymptomAgent:

    def __init__(self):
        self.name = "Symptom Recommendation Agent"

    def analyze_symptoms(self, symptoms):

        symptoms = symptoms.lower().strip()

        # Cardiologist
        if (
            "chest pain" in symptoms
            or "chest pressure" in symptoms
            or "heart pain" in symptoms
            or "palpitation" in symptoms
            or "palpitations" in symptoms
        ):
            return {
                "specialist": "Cardiologist",
                "message": "Based on the symptoms provided, we recommend consulting a Cardiologist.",
                "category": "cardiology"
            }

        # General Doctor
        elif (
            "fever" in symptoms
            or "cold" in symptoms
            or "cough" in symptoms
            or "flu" in symptoms
            or "sore throat" in symptoms
        ):
            return {
                "specialist": "General Doctor",
                "message": "Based on the symptoms provided, we recommend consulting a General Doctor.",
                "category": "general"
            }

        # Neurologist
        elif (
            "headache" in symptoms
            or "migraine" in symptoms
            or "dizziness" in symptoms
            or "vertigo" in symptoms
        ):
            return {
                "specialist": "Neurologist",
                "message": "Based on the symptoms provided, we recommend consulting a Neurologist.",
                "category": "neurology"
            }

        # Dermatologist
        elif (
            "skin problem" in symptoms
            or "skin" in symptoms
            or "rash" in symptoms
            or "acne" in symptoms
            or "itching" in symptoms
        ):
            return {
                "specialist": "Dermatologist",
                "message": "Based on the symptoms provided, we recommend consulting a Dermatologist.",
                "category": "dermatology"
            }

        # Gastroenterologist
        elif (
            "stomach pain" in symptoms
            or "abdominal pain" in symptoms
            or "vomiting" in symptoms
            or "indigestion" in symptoms
            or "gastric" in symptoms
        ):
            return {
                "specialist": "Gastroenterologist",
                "message": "Based on the symptoms provided, we recommend consulting a Gastroenterologist.",
                "category": "gastroenterology"
            }

        # Orthopedic
        elif (
            "bone pain" in symptoms
            or "joint pain" in symptoms
            or "back pain" in symptoms
            or "knee pain" in symptoms
            or "leg pain" in symptoms
        ):
            return {
                "specialist": "Orthopedic Specialist",
                "message": "Based on the symptoms provided, we recommend consulting an Orthopedic Specialist.",
                "category": "orthopedic"
            }

        # Ophthalmologist
        elif (
            "eye pain" in symptoms
            or "eye problem" in symptoms
            or "blurred vision" in symptoms
            or "vision problem" in symptoms
        ):
            return {
                "specialist": "Ophthalmologist",
                "message": "Based on the symptoms provided, we recommend consulting an Ophthalmologist.",
                "category": "ophthalmology"
            }

        # ENT
        elif (
            "ear pain" in symptoms
            or "hearing problem" in symptoms
            or "sinus" in symptoms
            or "nose problem" in symptoms
        ):
            return {
                "specialist": "ENT Specialist",
                "message": "Based on the symptoms provided, we recommend consulting an ENT Specialist.",
                "category": "ent"
            }

        # Default
        else:
            return {
                "specialist": "General Doctor",
                "message": "The symptoms need an initial evaluation. We recommend consulting a General Doctor.",
                "category": "general"
            }


# Create agent object
symptom_agent = SymptomAgent()