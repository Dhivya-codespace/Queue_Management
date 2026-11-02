from typing import TypedDict


class LocationState(TypedDict):
    patient_name: str
    location: str
    distance_km: float
    estimated_time: int
    location_status: str


def location_tracking_agent(
    state: LocationState
) -> LocationState:

    # Preserve calculated distance if present, otherwise default to demo 5.0 km
    raw_distance = state.get("distance_km")
    if raw_distance is not None and isinstance(raw_distance, (int, float)) and raw_distance >= 0:
        distance = float(raw_distance)
    else:
        distance = 5.0

    raw_time = state.get("estimated_time")
    if raw_time is not None and isinstance(raw_time, (int, float)) and raw_time > 0:
        estimated_time = int(raw_time)
    else:
        estimated_time = max(1, round(distance * 3))

    location_desc = state.get("location") or "Gandhipuram, Coimbatore (approximate demo location)"

    location_status = state.get("location_status")
    if not location_status:
        if distance <= 5:
            location_status = "Near Hospital"
        elif distance <= 15:
            location_status = "On the Way"
        else:
            location_status = "Far from Hospital"

    # Update state
    state["location"] = location_desc
    state["distance_km"] = distance
    state["estimated_time"] = estimated_time
    state["location_status"] = location_status

    # Terminal output
    print("\n====================================")
    print("      LOCATION TRACKING AGENT")
    print("====================================")
    print(f"Patient          : {state.get('patient_name', 'Patient')}")
    print(f"Location         : {location_desc}")
    print(f"Distance         : {distance} km")
    print(f"Estimated Time   : {estimated_time} minutes")
    print(f"Location Status  : {location_status}")
    print("====================================\n")

    return state