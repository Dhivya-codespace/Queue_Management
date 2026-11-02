from hospital.agents.supervisor import graph

result = graph.invoke(
    {
        "patient_name": "Dhivya",
        "doctor_name": "Dr. Kumar",
        "appointment_time": "10:00 AM",
        "symptoms": "Chest Pain",

        "booking_status": "",

        "risk_score": 92,

        "priority": "",
        "token_number": 0,
    }
)

print("\n==========================")
print("FINAL OUTPUT")
print("==========================")
print(result)