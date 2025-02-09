import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5, headless_mode=False):
        self.mp_hands = mp.solutions.hands.Hands(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = None  # Video capture object
        self.headless_mode = headless_mode  # Toggle for headless mode

    def start_detection(self):
        """Starts the webcam and begins detecting hands."""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)  # Set width
        self.cap.set(4, 720)   # Set height

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.mp_hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    self.draw_hand_pointer(frame, hand_landmarks)

            if not self.headless_mode:
                cv2.imshow('Hand Detection', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop_detection()

    def get_landmarks(self, frame):
        """Returns hand landmarks detected in the given frame."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.mp_hands.process(rgb_frame)
        return results.multi_hand_landmarks if results.multi_hand_landmarks else None

    def draw_landmarks(self, frame, landmarks):
        """Draws landmarks on the given frame."""
        if landmarks:
            for hand_landmarks in landmarks:
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

    def draw_hand_pointer(self, frame, hand_landmarks):
        """Draws a line from the palm to the index finger tip to indicate pointing direction."""
        h, w, _ = frame.shape
        palm_x, palm_y = int(hand_landmarks.landmark[0].x * w), int(hand_landmarks.landmark[0].y * h)
        finger_x, finger_y = int(hand_landmarks.landmark[8].x * w), int(hand_landmarks.landmark[8].y * h)

        cv2.line(frame, (palm_x, palm_y), (finger_x, finger_y), (0, 255, 0), 3)  # Green line
        cv2.circle(frame, (finger_x, finger_y), 8, (0, 0, 255), -1)  # Red circle

    def stop_detection(self):
        """Releases resources and closes windows."""
        if self.cap:
            self.cap.release()
        if not self.headless_mode:
            cv2.destroyAllWindows()
