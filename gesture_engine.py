"""
GestureEngine - The "Brain" of the Gesture Control System
Analyzes landmark vectors to determine user intent and gestures
"""

import time
import numpy as np
from typing import List, Dict, Optional, Tuple
import config
from hand_detector import HandObject, HandDetector


class GestureState:
    """Tracks the current state of detected gestures"""

    def __init__(self):
        self.cursor_position = None  # (x, y) of index finger
        self.is_clicking = False
        self.is_scrolling = False
        self.is_zooming = False
        self.is_paused = True  # Start in paused state for safety
        self.zoom_direction = None  # 'in' or 'out'
        self.air_push_detected = False
        self.active_hand = None  # Primary hand for cursor control
        self.both_hands_active = False
        self.fist_progress = 0.0  # Progress of fist hold (0.0 to 1.0)


class GestureEngine:
    """
    Analyzes hand landmarks to detect various gestures
    """

    def __init__(self, detector: HandDetector):
        """
        Initialize the gesture engine

        Args:
            detector: HandDetector instance
        """
        self.detector = detector
        self.state = GestureState()

        # Timing for debouncing and state tracking
        self.last_click_time = 0
        self.last_zoom_time = 0
        self.fist_start_time = None
        self.last_toggle_time = 0  # Track last pause toggle time
        self.toggle_cooldown = 1.5  # Cooldown period after toggle
        self.last_hand_area = 0
        self.area_change_time = 0

        # Previous positions for tracking movement
        self.prev_cursor_pos = None
        self.prev_zoom_distance = None

        # Scroll tracking
        self.scroll_start_y = None

    def analyze(self, hands: List[HandObject]) -> GestureState:
        """
        Analyze detected hands and update gesture state

        Args:
            hands: List of HandObject instances from HandDetector

        Returns:
            GestureState with current gesture information
        """
        # Reset per-frame states
        self.state.is_clicking = False
        self.state.is_scrolling = False
        self.state.is_zooming = False
        self.state.zoom_direction = None
        self.state.air_push_detected = False
        self.state.both_hands_active = len(hands) >= 2

        if not hands:
            # No hands detected
            self.state.cursor_position = None
            self.state.active_hand = None
            self.fist_start_time = None
            self.scroll_start_y = None
            return self.state

        # Primary hand (for single-hand gestures)
        primary_hand = hands[0]
        self.state.active_hand = primary_hand

        # Check for pause/resume gesture (fist)
        current_time = time.time()

        # Only process fist gesture if cooldown period has passed
        if current_time - self.last_toggle_time > self.toggle_cooldown:
            if self.detector.is_fist(primary_hand.lm_list):
                if self.fist_start_time is None:
                    self.fist_start_time = current_time
                    print(f"[DEBUG] Fist detected, starting timer...")
                else:
                    elapsed = current_time - self.fist_start_time
                    # Update progress (0.0 to 1.0)
                    self.state.fist_progress = min(1.0, elapsed / config.FIST_DURATION)

                    if elapsed >= config.FIST_DURATION:
                        # Toggle pause state
                        self.state.is_paused = not self.state.is_paused
                        mode = "ACTIVE" if not self.state.is_paused else "PAUSED"
                        print(f"[INFO] System toggled to {mode}")
                        self.fist_start_time = None
                        self.last_toggle_time = current_time
                        self.state.fist_progress = 0.0
            else:
                self.fist_start_time = None
                self.state.fist_progress = 0.0
        else:
            # In cooldown period
            self.state.fist_progress = 0.0

        # If paused, don't process other gestures
        if self.state.is_paused:
            return self.state

        # Update cursor position (index finger tip)
        index_tip = self.detector.get_landmark_by_id(
            primary_hand.lm_list,
            config.LANDMARK_INDEX_TIP
        )
        if index_tip:
            self.state.cursor_position = (index_tip[1], index_tip[2])

        # Detect pinch (click gesture)
        self._detect_pinch(primary_hand)

        # Detect scroll mode (high five + vertical movement)
        self._detect_scroll(primary_hand)

        # Detect air push (Z-axis movement)
        self._detect_air_push(primary_hand)

        # Detect two-hand zoom
        if len(hands) >= 2:
            self._detect_zoom(hands[0], hands[1])

        return self.state

    def _detect_pinch(self, hand: HandObject):
        """
        Detect pinch gesture (thumb + index finger close together)

        Args:
            hand: HandObject to analyze
        """
        thumb_tip = self.detector.get_landmark_by_id(
            hand.lm_list,
            config.LANDMARK_THUMB_TIP
        )
        index_tip = self.detector.get_landmark_by_id(
            hand.lm_list,
            config.LANDMARK_INDEX_TIP
        )

        if thumb_tip and index_tip:
            distance = self.detector.calculate_distance(thumb_tip, index_tip)

            # Check if distance is below threshold and debounce time has passed
            current_time = time.time()
            if (distance < config.PINCH_THRESHOLD and
                current_time - self.last_click_time > config.CLICK_DEBOUNCE_TIME):
                self.state.is_clicking = True
                self.last_click_time = current_time

    def _detect_scroll(self, hand: HandObject):
        """
        Detect scroll gesture (high five + vertical movement)

        Args:
            hand: HandObject to analyze
        """
        if self.detector.is_high_five(hand.lm_list):
            # Get current Y position of palm (wrist)
            wrist = self.detector.get_landmark_by_id(
                hand.lm_list,
                config.LANDMARK_WRIST
            )

            if wrist:
                current_y = wrist[2]

                if self.scroll_start_y is None:
                    self.scroll_start_y = current_y
                else:
                    # Calculate vertical movement
                    delta_y = current_y - self.scroll_start_y

                    # If movement exceeds threshold, enable scrolling
                    if abs(delta_y) > config.SCROLL_THRESHOLD:
                        self.state.is_scrolling = True
                        self.scroll_start_y = current_y
        else:
            self.scroll_start_y = None

    def _detect_zoom(self, hand1: HandObject, hand2: HandObject):
        """
        Detect zoom gesture (distance between index fingers of both hands)

        Args:
            hand1: First HandObject
            hand2: Second HandObject
        """
        index1 = self.detector.get_landmark_by_id(
            hand1.lm_list,
            config.LANDMARK_INDEX_TIP
        )
        index2 = self.detector.get_landmark_by_id(
            hand2.lm_list,
            config.LANDMARK_INDEX_TIP
        )

        if index1 and index2:
            current_distance = self.detector.calculate_distance(index1, index2)

            if self.prev_zoom_distance is not None:
                distance_change = current_distance - self.prev_zoom_distance

                # Check if change exceeds threshold and debounce time has passed
                current_time = time.time()
                if (abs(distance_change) > config.ZOOM_SENSITIVITY and
                    current_time - self.last_zoom_time > config.ZOOM_DEBOUNCE_TIME):

                    self.state.is_zooming = True

                    if distance_change > 0:
                        self.state.zoom_direction = 'out'  # Zoom out (hands moving apart)
                    else:
                        self.state.zoom_direction = 'in'  # Zoom in (hands moving together)

                    self.last_zoom_time = current_time

            self.prev_zoom_distance = current_distance
        else:
            self.prev_zoom_distance = None

    def _detect_air_push(self, hand: HandObject):
        """
        Detect air push gesture (hand moving quickly toward camera on Z-axis)

        Args:
            hand: HandObject to analyze
        """
        current_area = self.detector.get_hand_area(hand.lm_list)
        current_time = time.time()

        if self.last_hand_area > 0:
            area_increase = (current_area - self.last_hand_area) / self.last_hand_area

            # Check if area increased rapidly (hand moving forward)
            if area_increase > config.AIR_PUSH_AREA_THRESHOLD:
                time_since_change = current_time - self.area_change_time

                if time_since_change <= config.AIR_PUSH_TIME_WINDOW:
                    self.state.air_push_detected = True

                self.area_change_time = current_time

        self.last_hand_area = current_area

    def get_scroll_amount(self, hand: HandObject) -> int:
        """
        Calculate scroll amount based on hand movement

        Args:
            hand: HandObject to analyze

        Returns:
            Scroll amount (positive = down, negative = up)
        """
        if not self.state.is_scrolling:
            return 0

        wrist = self.detector.get_landmark_by_id(
            hand.lm_list,
            config.LANDMARK_WRIST
        )

        if wrist and self.scroll_start_y is not None:
            delta_y = wrist[2] - self.scroll_start_y
            return int(delta_y / config.SCROLL_SENSITIVITY)

        return 0

    def reset(self):
        """Reset gesture engine state"""
        self.state = GestureState()
        self.last_click_time = 0
        self.last_zoom_time = 0
        self.fist_start_time = None
        self.last_hand_area = 0
        self.area_change_time = 0
        self.prev_cursor_pos = None
        self.prev_zoom_distance = None
        self.scroll_start_y = None
