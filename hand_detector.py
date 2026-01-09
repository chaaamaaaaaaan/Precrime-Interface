"""
HandDetector - MediaPipe Wrapper for Hand Detection
Provides a clean interface for detecting hands and extracting landmarks
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Optional, Tuple
import config


class HandObject:
    """Represents a detected hand with its landmarks and metadata"""

    def __init__(self, landmarks, handedness, hand_index):
        self.landmarks = landmarks  # List of landmark objects
        self.handedness = handedness  # 'Left' or 'Right'
        self.hand_index = hand_index  # 0 or 1
        self.lm_list = []  # Will store [id, x, y, z] for each landmark

    def set_landmark_list(self, lm_list):
        """Set the processed landmark list with pixel coordinates"""
        self.lm_list = lm_list


class HandDetector:
    """
    Wrapper for MediaPipe Hands solution
    Provides methods to detect hands and extract landmarks
    """

    def __init__(self,
                 max_hands=config.MAX_NUM_HANDS,
                 detection_confidence=config.MIN_DETECTION_CONFIDENCE,
                 tracking_confidence=config.MIN_TRACKING_CONFIDENCE):
        """
        Initialize the hand detector

        Args:
            max_hands: Maximum number of hands to detect
            detection_confidence: Minimum confidence for detection
            tracking_confidence: Minimum confidence for tracking
        """
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )

        self.mp_draw = mp.solutions.drawing_utils
        self.results = None

    def find_hands(self, frame, draw=False) -> List[HandObject]:
        """
        Detect hands in the frame and return list of HandObject instances

        Args:
            frame: BGR image from camera
            draw: Whether to draw MediaPipe default landmarks

        Returns:
            List of HandObject instances
        """
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame
        self.results = self.hands.process(frame_rgb)

        hand_objects = []

        # If hands are detected
        if self.results.multi_hand_landmarks:
            for hand_idx, (hand_landmarks, handedness) in enumerate(
                zip(self.results.multi_hand_landmarks, self.results.multi_handedness)
            ):
                # Get handedness label (Left or Right)
                hand_label = handedness.classification[0].label

                # Create HandObject
                hand_obj = HandObject(hand_landmarks, hand_label, hand_idx)

                # Extract landmark positions
                h, w, c = frame.shape
                lm_list = []

                for lm_id, landmark in enumerate(hand_landmarks.landmark):
                    # Convert normalized coordinates to pixel coordinates
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    z = landmark.z  # Depth (relative to wrist)

                    lm_list.append([lm_id, x, y, z])

                hand_obj.set_landmark_list(lm_list)
                hand_objects.append(hand_obj)

                # Optional: Draw default MediaPipe landmarks
                if draw:
                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )

        return hand_objects

    def find_position(self, frame, hand_no=0) -> List[List]:
        """
        Find landmark positions for a specific hand

        Args:
            frame: BGR image from camera
            hand_no: Which hand to get positions for (0 or 1)

        Returns:
            List of [id, x, y, z] for each landmark, or empty list if hand not found
        """
        lm_list = []

        if self.results and self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                hand_landmarks = self.results.multi_hand_landmarks[hand_no]
                h, w, c = frame.shape

                for lm_id, landmark in enumerate(hand_landmarks.landmark):
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    z = landmark.z
                    lm_list.append([lm_id, x, y, z])

        return lm_list

    def get_landmark_by_id(self, lm_list: List[List], lm_id: int) -> Optional[Tuple[int, int, int, float]]:
        """
        Get a specific landmark from the landmark list

        Args:
            lm_list: List of landmarks [id, x, y, z]
            lm_id: ID of the landmark to retrieve

        Returns:
            Tuple of (id, x, y, z) or None if not found
        """
        for landmark in lm_list:
            if landmark[0] == lm_id:
                return tuple(landmark)
        return None

    def calculate_distance(self, p1: Tuple, p2: Tuple) -> float:
        """
        Calculate Euclidean distance between two points

        Args:
            p1: First point (id, x, y, z) or (x, y)
            p2: Second point (id, x, y, z) or (x, y)

        Returns:
            Distance in pixels
        """
        # Handle both (x, y) and (id, x, y, z) formats
        if len(p1) > 2:
            x1, y1 = p1[1], p1[2]
        else:
            x1, y1 = p1[0], p1[1]

        if len(p2) > 2:
            x2, y2 = p2[1], p2[2]
        else:
            x2, y2 = p2[0], p2[1]

        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return distance

    def get_hand_bounding_box(self, lm_list: List[List]) -> Tuple[int, int, int, int]:
        """
        Get bounding box for a hand

        Args:
            lm_list: List of landmarks [id, x, y, z]

        Returns:
            Tuple of (x_min, y_min, x_max, y_max)
        """
        if not lm_list:
            return (0, 0, 0, 0)

        x_coords = [lm[1] for lm in lm_list]
        y_coords = [lm[2] for lm in lm_list]

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def get_hand_area(self, lm_list: List[List]) -> float:
        """
        Calculate the area of the hand bounding box

        Args:
            lm_list: List of landmarks [id, x, y, z]

        Returns:
            Area in square pixels
        """
        x_min, y_min, x_max, y_max = self.get_hand_bounding_box(lm_list)
        width = x_max - x_min
        height = y_max - y_min
        return width * height

    def is_fist(self, lm_list: List[List]) -> bool:
        """
        Detect if hand is in a fist position (all fingers closed)

        Args:
            lm_list: List of landmarks [id, x, y, z]

        Returns:
            True if fist detected
        """
        if len(lm_list) < 21:
            return False

        # Get wrist position
        wrist = lm_list[config.LANDMARK_WRIST]

        # Check if all fingertips are close to wrist (normalized by hand size)
        x_min, y_min, x_max, y_max = self.get_hand_bounding_box(lm_list)
        hand_size = max(x_max - x_min, y_max - y_min)

        if hand_size == 0:
            return False

        closed_fingers = 0

        # Check each finger separately with improved logic
        # For each finger, check if tip is closer to wrist than the MCP joint (knuckle)
        finger_landmarks = [
            (4, 2),   # Thumb: tip vs CMC joint
            (8, 5),   # Index: tip vs MCP joint
            (12, 9),  # Middle: tip vs MCP joint
            (16, 13), # Ring: tip vs MCP joint
            (20, 17)  # Pinky: tip vs MCP joint
        ]

        for tip_id, base_id in finger_landmarks:
            tip = lm_list[tip_id]
            base = lm_list[base_id]

            # Distance from tip to wrist
            tip_to_wrist = self.calculate_distance(wrist, tip)
            # Distance from base to wrist
            base_to_wrist = self.calculate_distance(wrist, base)

            # If tip is closer to wrist than base, or very close to base, finger is closed
            # Also check normalized distance as backup
            normalized_distance = tip_to_wrist / hand_size if hand_size > 0 else 0

            # Balanced detection: tip must be closer or equal to base distance
            if (tip_to_wrist <= base_to_wrist) or (normalized_distance < config.FIST_THRESHOLD):
                closed_fingers += 1

        # At least 4 fingers must be closed for a fist (balanced requirement)
        return closed_fingers >= 4

    def is_high_five(self, lm_list: List[List]) -> bool:
        """
        Detect if hand is in "high five" pose (all fingers extended)

        Args:
            lm_list: List of landmarks [id, x, y, z]

        Returns:
            True if high five detected
        """
        if len(lm_list) < 21:
            return False

        # Get palm base (wrist)
        wrist = lm_list[config.LANDMARK_WRIST]

        # Get hand size for normalization
        x_min, y_min, x_max, y_max = self.get_hand_bounding_box(lm_list)
        hand_size = max(x_max - x_min, y_max - y_min)

        if hand_size == 0:
            return False

        extended_fingers = 0
        for tip_id in config.FINGERTIP_IDS:
            tip = lm_list[tip_id]
            distance = self.calculate_distance(wrist, tip)
            normalized_distance = distance / hand_size

            # If fingertip is far from wrist, finger is extended
            if normalized_distance > 0.55:  # Threshold for extended finger (lowered for better sensitivity)
                extended_fingers += 1

        # At least 3 fingers must be extended for high five (lowered for better sensitivity)
        return extended_fingers >= 3

    def close(self):
        """Clean up resources"""
        self.hands.close()
