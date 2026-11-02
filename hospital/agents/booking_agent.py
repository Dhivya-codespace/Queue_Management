from typing import TypedDict


class BookingState(TypedDict):
    patient_name: str
    doctor_name: str
    appointment_time: str
    symptoms: str
    booking_status: str


def booking_agent(state: BookingState) -> BookingState:
    """
    Books the appointment.
    """

    state["booking_status"] = "Appointment Booked Successfully"

    print("\n===== Booking Agent =====")
    print(f"Patient : {state['patient_name']}")
    print(f"Doctor  : {state['doctor_name']}")
    print(f"Time    : {state['appointment_time']}")
    print(f"Status  : {state['booking_status']}")

    return state