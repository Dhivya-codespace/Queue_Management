from typing import TypedDict


class DoctorAvailabilityState(TypedDict):
    doctor_name: str
    doctor_available: bool


def doctor_availability_agent(
    state: DoctorAvailabilityState
) -> DoctorAvailabilityState:

    doctor = state["doctor_name"]

    # Doctors currently available
    available_doctors = [
        "Dr. Kumar",
        "Dr. Priya",
    ]

    if doctor in available_doctors:
        state["doctor_available"] = True
    else:
        state["doctor_available"] = False

    print("\n===== Doctor Availability Agent =====")
    print(f"Doctor : {doctor}")
    print(f"Available : {state['doctor_available']}")

    return state