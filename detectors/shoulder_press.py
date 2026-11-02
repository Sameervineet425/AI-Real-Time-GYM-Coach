
from core.base_exercise import BaseExercise


class ShoulderPressDetector(BaseExercise):
    UP_THRESHOLD = 120
    DOWN_THRESHOLD = 80
    MIN_VISIBILITY = 0.3

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def __init__(self):
        super().__init__()
        self.reps = 0
        self.stage = None

    def reset(self):
        self.reps = 0
        self.stage = None

    def process(self, landmarks):
        left_indices = [
            self.LEFT_SHOULDER,
            self.LEFT_ELBOW,
            self.LEFT_WRIST,
            self.LEFT_HIP
        ]

        right_indices = [
            self.RIGHT_SHOULDER,
            self.RIGHT_ELBOW,
            self.RIGHT_WRIST,
            self.RIGHT_HIP
        ]

        left_visibility = sum(landmarks[i].visibility for i in left_indices)
        right_visibility = sum(landmarks[i].visibility for i in right_indices)

        if left_visibility >= right_visibility:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
            hip_idx = self.LEFT_HIP
            knee_idx = self.LEFT_KNEE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST
            hip_idx = self.RIGHT_HIP
            knee_idx = self.RIGHT_KNEE

        # Calculate shoulder angle
        shoulder_angle = self.calculate_angle(
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx)
        )

        # Calculate elbow angle
        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx)
        )

        # Check landmark visibility
        shoulder_vis = landmarks[shoulder_idx].visibility
        elbow_vis = landmarks[elbow_idx].visibility
        wrist_vis = landmarks[wrist_idx].visibility

        visible = (
            shoulder_vis > self.MIN_VISIBILITY
            and elbow_vis > self.MIN_VISIBILITY
            and wrist_vis > self.MIN_VISIBILITY
        )

        # Repetition counting
        if visible:
            if shoulder_angle <= self.DOWN_THRESHOLD:
                self.stage = "down"

            elif shoulder_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.reps += 1
                self.stage = "up"

        # Debug information
        print(
            f"[SHOULDER PRESS] "
            f"Shoulder Angle: {shoulder_angle:.2f} | "
            f"Elbow Angle: {elbow_angle:.2f} | "
            f"Stage: {self.stage} | "
            f"Reps: {self.reps} | "
            f"Visible: {visible}"
        )

        # Extension status
        if elbow_angle >= 160:
            extension_status = "FULL EXTENSION"
        elif elbow_angle >= 130:
            extension_status = "NEARLY EXTENDED"
        elif elbow_angle >= 90:
            extension_status = "PRESSING"
        else:
            extension_status = "START POSITION"

        # Back angle
        back_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx)
        )

        if back_angle >= 160:
            back_arch_status = "Neutral"
        elif back_angle >= 140:
            back_arch_status = "Slight Arch"
        else:
            back_arch_status = "Excessive Arch"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_angle": int(shoulder_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status
        }
