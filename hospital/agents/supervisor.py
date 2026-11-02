from typing import TypedDict

from langgraph.graph import StateGraph, END

from hospital.agents.booking_agent import booking_agent
from hospital.agents.doctor_availability_agent import doctor_availability_agent
from hospital.agents.location_tracking_agent import location_tracking_agent
from hospital.agents.risk_agent import risk_agent
from hospital.agents.queue_agent import queue_agent
from hospital.agents.notification_agent import notification_agent


class HospitalState(TypedDict):
    patient_name: str
    doctor_name: str
    appointment_time: str
    symptoms: str
    booking_status: str

    doctor_available: bool

    location: str
    distance_km: float
    estimated_time: int
    location_status: str

    risk_score: int
    priority: str
    token_number: int

    # Current token being served
    current_token: int

    # Queue waiting information
    patients_before: int
    estimated_wait_time: int

    # Notification
    notification_message: str


builder = StateGraph(HospitalState)


# ================= AGENTS =================

builder.add_node(
    "booking_agent",
    booking_agent
)

builder.add_node(
    "doctor_availability_agent",
    doctor_availability_agent
)

builder.add_node(
    "location_tracking_agent",
    location_tracking_agent
)

builder.add_node(
    "risk_agent",
    risk_agent
)

builder.add_node(
    "queue_agent",
    queue_agent
)

builder.add_node(
    "notification_agent",
    notification_agent
)


# ================= START =================

builder.set_entry_point("booking_agent")


# ================= AGENT FLOW =================

builder.add_edge(
    "booking_agent",
    "doctor_availability_agent"
)

builder.add_edge(
    "doctor_availability_agent",
    "location_tracking_agent"
)

builder.add_edge(
    "location_tracking_agent",
    "risk_agent"
)

builder.add_edge(
    "risk_agent",
    "queue_agent"
)

builder.add_edge(
    "queue_agent",
    "notification_agent"
)

builder.add_edge(
    "notification_agent",
    END
)


# ================= COMPILE =================

graph = builder.compile()