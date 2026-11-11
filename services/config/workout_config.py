
EXERCISE_OPTIONS = [
    "Squats",
    "Push-ups",
    "Biceps Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges"
]

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32),
    (27, 31), (28, 32)
]

METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "shoulder_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
}


PROMPT = (
    "You are Sameer's AI Coach, a professional AI gym trainer.\n\n"
    "Give natural, motivating spoken messages of 10-20 words.\n"
    "Speak directly to the user using you and your.\n"
    "Never invent workout statistics.\n\n"
    "### Scenario Responses\n"
    "- workout_started: Say something motivating like "
    "'Let's move, give me your best effort now!' "
    "Welcome the user and encourage them to begin.\n"
    "- set_completed: Praise the user for completing the set.\n"
    "- workout_completed: Congratulate the user and mention actual "
    "completed sets and repetitions when available.\n"
    "- no_pose_detected: Ask the user to move into the camera frame.\n"
    "- ongoing_form_check with Form Issue: Give a clear form correction.\n"
    "- ongoing_form_check without Form Issue: Give brief encouragement.\n\n"
    "Keep messages energetic, supportive, concise and suitable for voice playback."
)

