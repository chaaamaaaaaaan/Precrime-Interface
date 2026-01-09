"""
HoloHUD - Sci-Fi Visual Overlay System
Renders "Minority Report" style visual effects on the video feed
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional
import config
from hand_detector import HandObject
from gesture_engine import GestureState


class HoloHUD:
    """
    Renders a futuristic heads-up display over the camera feed
    with Minority Report aesthetic
    """

    def __init__(self, frame_width: int, frame_height: int):
        """
        Initialize the HUD

        Args:
            frame_width: Width of video frame
            frame_height: Height of video frame
        """
        self.frame_width = frame_width
        self.frame_height = frame_height

        # FPS calculation
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        self.fps = 0

        # Animation state
        self.pulse_phase = 0

    def render(self,
               frame: np.ndarray,
               hands: List[HandObject],
               gesture_state: GestureState) -> np.ndarray:
        """
        Render the complete HUD on the frame

        Args:
            frame: BGR image from camera
            hands: List of detected HandObject instances
            gesture_state: Current gesture state

        Returns:
            Frame with HUD overlay
        """
        # Create overlay for transparency effects
        overlay = frame.copy()

        # Draw hand landmarks and connections
        for hand in hands:
            self._draw_hand_skeleton(overlay, hand, gesture_state)
            self._draw_fingertips(overlay, hand, gesture_state)

        # Draw interaction region boundary
        self._draw_interaction_region(overlay)

        # Blend overlay with original frame for transparency
        cv2.addWeighted(overlay, config.HUD_LINE_ALPHA, frame, 1 - config.HUD_LINE_ALPHA, 0, frame)

        # Draw UI elements (text, status, etc.)
        self._draw_status_indicator(frame, gesture_state)
        self._draw_fist_progress(frame, gesture_state)
        self._draw_fps_counter(frame)
        self._draw_gesture_info(frame, gesture_state)

        # Update animation
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * np.pi)

        return frame

    def _draw_hand_skeleton(self,
                           frame: np.ndarray,
                           hand: HandObject,
                           gesture_state: GestureState):
        """
        Draw hand connections with sci-fi aesthetic

        Args:
            frame: Frame to draw on
            hand: HandObject with landmarks
            gesture_state: Current gesture state
        """
        lm_list = hand.lm_list

        if len(lm_list) < 21:
            return

        # Choose color based on hand state
        if gesture_state.is_clicking:
            color = config.HUD_COLOR_CLICKING
        elif gesture_state.is_paused:
            color = (128, 128, 128)  # Gray when paused
        else:
            color = config.HUD_COLOR_PRIMARY

        # Draw connections
        for connection in config.HAND_CONNECTIONS:
            start_idx, end_idx = connection

            if start_idx < len(lm_list) and end_idx < len(lm_list):
                start = lm_list[start_idx]
                end = lm_list[end_idx]

                start_point = (start[1], start[2])
                end_point = (end[1], end[2])

                # Draw line with glow effect
                self._draw_glow_line(frame, start_point, end_point, color)

    def _draw_glow_line(self,
                       frame: np.ndarray,
                       start: Tuple[int, int],
                       end: Tuple[int, int],
                       color: Tuple[int, int, int]):
        """
        Draw a line with a subtle glow effect

        Args:
            frame: Frame to draw on
            start: Start point (x, y)
            end: End point (x, y)
            color: Line color (BGR)
        """
        # Draw outer glow (thicker, darker)
        darker_color = tuple(int(c * 0.5) for c in color)
        cv2.line(frame, start, end, darker_color, config.HUD_LINE_THICKNESS + 2)

        # Draw main line
        cv2.line(frame, start, end, color, config.HUD_LINE_THICKNESS)

    def _draw_fingertips(self,
                        frame: np.ndarray,
                        hand: HandObject,
                        gesture_state: GestureState):
        """
        Draw circles on fingertips with depth-based sizing

        Args:
            frame: Frame to draw on
            hand: HandObject with landmarks
            gesture_state: Current gesture state
        """
        lm_list = hand.lm_list

        for tip_id in config.FINGERTIP_IDS:
            if tip_id < len(lm_list):
                tip = lm_list[tip_id]
                x, y, z = tip[1], tip[2], tip[3]

                # Adjust radius based on depth (z-coordinate)
                # Negative z means closer to camera
                radius = int(config.HUD_CIRCLE_RADIUS_BASE + config.HUD_CIRCLE_RADIUS_DEPTH_SCALE * abs(z))
                radius = max(5, min(radius, 20))  # Clamp radius

                # Choose color
                if tip_id == config.LANDMARK_INDEX_TIP and gesture_state.cursor_position:
                    color = config.HUD_COLOR_ACTIVE  # Green for cursor
                elif gesture_state.is_clicking:
                    color = config.HUD_COLOR_CLICKING  # Magenta for clicking
                else:
                    color = config.HUD_COLOR_PRIMARY  # Cyan default

                # Draw circle with glow
                self._draw_glow_circle(frame, (x, y), radius, color)

    def _draw_glow_circle(self,
                         frame: np.ndarray,
                         center: Tuple[int, int],
                         radius: int,
                         color: Tuple[int, int, int]):
        """
        Draw a circle with glow effect

        Args:
            frame: Frame to draw on
            center: Center point (x, y)
            radius: Circle radius
            color: Circle color (BGR)
        """
        # Outer glow
        darker_color = tuple(int(c * 0.5) for c in color)
        cv2.circle(frame, center, radius + 2, darker_color, -1)

        # Inner circle
        cv2.circle(frame, center, radius, color, -1)

        # Bright center
        cv2.circle(frame, center, max(1, radius // 2), (255, 255, 255), -1)

    def _draw_interaction_region(self, frame: np.ndarray):
        """
        Draw the boundary of the interaction region

        Args:
            frame: Frame to draw on
        """
        # Calculate region boundaries
        x1 = int(self.frame_width * config.INTERACTION_REGION_X)
        y1 = int(self.frame_height * config.INTERACTION_REGION_Y)
        x2 = int(self.frame_width * (config.INTERACTION_REGION_X + config.INTERACTION_REGION_WIDTH))
        y2 = int(self.frame_height * (config.INTERACTION_REGION_Y + config.INTERACTION_REGION_HEIGHT))

        # Draw dashed rectangle
        color = (100, 100, 100)  # Dark gray
        thickness = 1

        # Draw corners only for minimal look
        corner_length = 30

        # Top-left
        cv2.line(frame, (x1, y1), (x1 + corner_length, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_length), color, thickness)

        # Top-right
        cv2.line(frame, (x2, y1), (x2 - corner_length, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_length), color, thickness)

        # Bottom-left
        cv2.line(frame, (x1, y2), (x1 + corner_length, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_length), color, thickness)

        # Bottom-right
        cv2.line(frame, (x2, y2), (x2 - corner_length, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_length), color, thickness)

    def _draw_fist_progress(self, frame: np.ndarray, gesture_state: GestureState):
        """
        Draw fist hold progress bar

        Args:
            frame: Frame to draw on
            gesture_state: Current gesture state
        """
        if gesture_state.fist_progress > 0:
            # Progress bar dimensions
            bar_width = 300
            bar_height = 20
            bar_x = (self.frame_width - bar_width) // 2
            bar_y = self.frame_height - 80

            # Background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                         (50, 50, 50), -1)

            # Progress bar
            progress_width = int(bar_width * gesture_state.fist_progress)
            color = config.HUD_COLOR_PRIMARY  # Cyan
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height),
                         color, -1)

            # Border
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                         config.HUD_COLOR_TEXT, 2)

            # Text
            text = "Hold fist to toggle..."
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = (self.frame_width - text_size[0]) // 2
            text_y = bar_y - 10

            cv2.putText(frame, text, (text_x, text_y),
                       font, font_scale, config.HUD_COLOR_TEXT, thickness)

    def _draw_status_indicator(self, frame: np.ndarray, gesture_state: GestureState):
        """
        Draw system status at bottom center

        Args:
            frame: Frame to draw on
            gesture_state: Current gesture state
        """
        # Status text
        if gesture_state.is_paused:
            status_text = "SAFE MODE"
            status_color = (0, 0, 255)  # Red
        else:
            status_text = "SYSTEM ACTIVE"
            status_color = config.HUD_COLOR_ACTIVE  # Green

        # Add pulsing effect when active
        if not gesture_state.is_paused:
            pulse = int(30 * np.sin(self.pulse_phase))
            status_color = tuple(min(255, c + pulse) for c in status_color)

        # Calculate text size and position
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        thickness = 2
        text_size = cv2.getTextSize(status_text, font, font_scale, thickness)[0]

        # Center bottom
        text_x = (self.frame_width - text_size[0]) // 2
        text_y = self.frame_height - 30

        # Draw text with shadow
        shadow_offset = 2
        cv2.putText(frame, status_text, (text_x + shadow_offset, text_y + shadow_offset),
                   font, font_scale, (0, 0, 0), thickness + 1)
        cv2.putText(frame, status_text, (text_x, text_y),
                   font, font_scale, status_color, thickness)

    def _draw_fps_counter(self, frame: np.ndarray):
        """
        Draw FPS counter in top-right corner

        Args:
            frame: Frame to draw on
        """
        # Calculate FPS
        self.fps_frame_count += 1
        elapsed_time = time.time() - self.fps_start_time

        if elapsed_time > 0.5:  # Update every 0.5 seconds
            self.fps = self.fps_frame_count / elapsed_time
            self.fps_frame_count = 0
            self.fps_start_time = time.time()

        # Draw FPS
        fps_text = f"FPS: {int(self.fps)}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1

        text_size = cv2.getTextSize(fps_text, font, font_scale, thickness)[0]
        text_x = self.frame_width - text_size[0] - 10
        text_y = 30

        # Draw with shadow
        cv2.putText(frame, fps_text, (text_x + 1, text_y + 1),
                   font, font_scale, (0, 0, 0), thickness + 1)
        cv2.putText(frame, fps_text, (text_x, text_y),
                   font, font_scale, config.HUD_COLOR_PRIMARY, thickness)

    def _draw_gesture_info(self, frame: np.ndarray, gesture_state: GestureState):
        """
        Draw current gesture information

        Args:
            frame: Frame to draw on
            gesture_state: Current gesture state
        """
        if gesture_state.is_paused:
            return

        gestures = []

        if gesture_state.is_clicking:
            gestures.append("CLICK")
        if gesture_state.is_scrolling:
            gestures.append("SCROLL")
        if gesture_state.is_zooming:
            gestures.append(f"ZOOM {gesture_state.zoom_direction.upper()}")
        if gesture_state.air_push_detected:
            gestures.append("AIR PUSH")

        if not gestures:
            return

        # Draw gesture info in top-left
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1
        y_offset = 30

        for i, gesture in enumerate(gestures):
            text = f"[{gesture}]"
            y_pos = y_offset + (i * 30)

            # Draw with shadow
            cv2.putText(frame, text, (11, y_pos + 1),
                       font, font_scale, (0, 0, 0), thickness + 1)
            cv2.putText(frame, text, (10, y_pos),
                       font, font_scale, config.HUD_COLOR_ACTIVE, thickness)

    def draw_crosshair(self, frame: np.ndarray, position: Tuple[int, int], size: int = 20):
        """
        Draw a crosshair at the cursor position

        Args:
            frame: Frame to draw on
            position: (x, y) position
            size: Size of crosshair
        """
        x, y = position
        color = config.HUD_COLOR_ACTIVE

        # Horizontal line
        cv2.line(frame, (x - size, y), (x + size, y), color, 2)
        # Vertical line
        cv2.line(frame, (x, y - size), (x, y + size), color, 2)
        # Center dot
        cv2.circle(frame, (x, y), 3, color, -1)
