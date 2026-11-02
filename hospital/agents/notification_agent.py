def notification_agent(state):

    patient_name = state["patient_name"]
    token_number = state["token_number"]

    # Current token being served
    current_token = state.get("current_token", 1)

    # Average consultation time
    consultation_time = 8

    # Calculate patients before this patient
    patients_before = token_number - current_token - 1

    if patients_before < 0:
        patients_before = 0

    # Calculate estimated waiting time
    estimated_wait_time = patients_before * consultation_time

    # Save values
    state["patients_before"] = patients_before
    state["estimated_wait_time"] = estimated_wait_time

    # -----------------------------------------
    # Smart reminder
    # -----------------------------------------

    if patients_before == 3:

        message = (
            f"Hello {patient_name}, there are 3 patients ahead of you. "
            f"Please plan your arrival and be ready."
        )

    elif patients_before == 2:

        message = (
            f"Hello {patient_name}, there are 2 patients ahead of you. "
            f"Please arrive at the hospital on time."
        )

    else:

        message = ""

    state["notification_message"] = message

    print("\n===== Notification Agent =====")
    print("Patient :", patient_name)
    print("Current Token :", current_token)
    print("Your Token :", token_number)
    print("Patients Before :", patients_before)
    print("Estimated Wait :", estimated_wait_time, "minutes")

    if message:
        print("Reminder :", message)
    else:
        print("Reminder : No reminder")

    return state