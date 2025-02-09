import cv2
import mediapipe as mp
import logging
import sys
import warnings
import os

logging.getLogger("tensorflow").setLevel(logging.ERROR)
logging.getLogger("absl").setLevel(logging.ERROR)
sys.stderr = open(os.devnull, 'w')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
warnings.filterwarnings("ignore")

class FaceHandDetector:
    def __init__(self, face_confidence=0.9, hand_confidence=0.9):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=face_confidence,
            min_tracking_confidence=face_confidence
        )
        self.hands = self.mp_hands.Hands(
            min_detection_confidence=hand_confidence,
            min_tracking_confidence=hand_confidence
        )
        
        self.previous_face_state = None
        self.previous_left_hand = None
        self.previous_right_hand = None
    
    def detect_face(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = self.face_mesh.process(rgb_frame)
        return face_results.multi_face_landmarks is not None
    
    def detect_hands(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = self.hands.process(rgb_frame)
        left_hand_detected = False
        right_hand_detected = False
        
        if hand_results.multi_handedness:
            for classification in hand_results.multi_handedness:
                label = classification.classification[0].label
                if label == "Left":
                    left_hand_detected = True
                elif label == "Right":
                    right_hand_detected = True
        
        return left_hand_detected, right_hand_detected
    
    def check_changes(self, face_detected, left_hand_detected, right_hand_detected):
        changes = []
        
        if face_detected != self.previous_face_state:
            changes.append(f"Face Detected: {face_detected}")
            self.previous_face_state = face_detected
        
        if left_hand_detected != self.previous_left_hand:
            changes.append(f"Left Hand Detected: {left_hand_detected}")
            self.previous_left_hand = left_hand_detected
        
        if right_hand_detected != self.previous_right_hand:
            changes.append(f"Right Hand Detected: {right_hand_detected}")
            self.previous_right_hand = right_hand_detected
        
        return changes
    
    def run_continuous(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Faster webcam access
        if not cap.isOpened():
            print("Error: Could not access the webcam.")
            return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Mirror the camera frame before any processing
            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            
            face_detected = self.detect_face(frame)
            left_hand_detected, right_hand_detected = self.detect_hands(frame)
            
            changes = self.check_changes(face_detected, left_hand_detected, right_hand_detected)
            if changes:
                print(" | ".join(changes))
            
            cv2.imshow("Face and Hand Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = FaceHandDetector()
    detector.run_continuous()
