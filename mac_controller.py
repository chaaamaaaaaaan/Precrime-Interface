"""
MacController - System Control Interface
Maps camera coordinates to screen coordinates and executes system actions
"""

import pyautogui
import time
import platform
from typing import Tuple, Optional
import config


class MacController:
    """
    Controls the system (mouse, keyboard) based on gesture input
    Implements smoothing and coordinate mapping
    """

    def __init__(self, camera_width: int, camera_height: int):
        """
        Initialize the controller

        Args:
            camera_width: Width of camera frame
            camera_height: Height of camera frame
        """
        self.camera_width = camera_width
        self.camera_height = camera_height

        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()

        # Configure PyAutoGUI
        pyautogui.FAILSAFE = config.FAILSAFE_ENABLED
        pyautogui.PAUSE = 0.01  # Minimal pause between commands

        # Smoothing state
        self.smooth_x = None
        self.smooth_y = None

        # Calculate interaction region boundaries in camera coordinates
        self.interaction_x_min = int(camera_width * config.INTERACTION_REGION_X)
        self.interaction_y_min = int(camera_height * config.INTERACTION_REGION_Y)
        self.interaction_x_max = int(camera_width * (config.INTERACTION_REGION_X + config.INTERACTION_REGION_WIDTH))
        self.interaction_y_max = int(camera_height * (config.INTERACTION_REGION_Y + config.INTERACTION_REGION_HEIGHT))

        # Platform detection
        self.is_mac = platform.system() == 'Darwin'

        print(f"[MacController] Initialized")
        print(f"  Screen: {self.screen_width}x{self.screen_height}")
        print(f"  Camera: {self.camera_width}x{self.camera_height}")
        print(f"  Platform: {platform.system()}")

    def get_screen_coords(self, cam_x: int, cam_y: int) -> Tuple[int, int]:
        """
        Map camera coordinates to screen coordinates with smoothing

        Args:
            cam_x: X coordinate in camera frame
            cam_y: Y coordinate in camera frame

        Returns:
            Tuple of (screen_x, screen_y)
        """
        # Clamp to interaction region
        cam_x = max(self.interaction_x_min, min(cam_x, self.interaction_x_max))
        cam_y = max(self.interaction_y_min, min(cam_y, self.interaction_y_max))

        # Normalize to [0, 1] within interaction region
        norm_x = (cam_x - self.interaction_x_min) / (self.interaction_x_max - self.interaction_x_min)
        norm_y = (cam_y - self.interaction_y_min) / (self.interaction_y_max - self.interaction_y_min)

        # Mirror X coordinate (camera is mirrored)
        norm_x = 1.0 - norm_x

        # Map to screen coordinates
        raw_screen_x = int(norm_x * self.screen_width)
        raw_screen_y = int(norm_y * self.screen_height)

        # Apply Exponential Moving Average (EMA) smoothing
        if self.smooth_x is None or self.smooth_y is None:
            # Initialize smoothing
            self.smooth_x = raw_screen_x
            self.smooth_y = raw_screen_y
        else:
            # Apply EMA formula: current = prev + (raw - prev) * alpha
            self.smooth_x = self.smooth_x + (raw_screen_x - self.smooth_x) * config.SMOOTHING_ALPHA
            self.smooth_y = self.smooth_y + (raw_screen_y - self.smooth_y) * config.SMOOTHING_ALPHA

        # Return smoothed coordinates
        return int(self.smooth_x), int(self.smooth_y)

    def move_cursor(self, cam_x: int, cam_y: int):
        """
        Move cursor to screen position corresponding to camera coordinates

        Args:
            cam_x: X coordinate in camera frame
            cam_y: Y coordinate in camera frame
        """
        screen_x, screen_y = self.get_screen_coords(cam_x, cam_y)

        try:
            pyautogui.moveTo(screen_x, screen_y, duration=0)
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered!")
            raise

    def click(self):
        """Execute a left mouse click"""
        try:
            pyautogui.click()
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during click!")
            raise

    def scroll(self, amount: int):
        """
        Scroll vertically

        Args:
            amount: Scroll amount (positive = down, negative = up)
        """
        try:
            # PyAutoGUI scroll is inverted (positive = up)
            pyautogui.scroll(-amount)
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during scroll!")
            raise

    def zoom_in(self):
        """Execute zoom in command (Cmd/Ctrl + +)"""
        try:
            if self.is_mac:
                pyautogui.hotkey('command', '=')  # Cmd + = (which is Cmd + +)
            else:
                pyautogui.hotkey('ctrl', '=')
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during zoom!")
            raise

    def zoom_out(self):
        """Execute zoom out command (Cmd/Ctrl + -)"""
        try:
            if self.is_mac:
                pyautogui.hotkey('command', '-')  # Cmd + -
            else:
                pyautogui.hotkey('ctrl', '-')
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during zoom!")
            raise

    def press_enter(self):
        """Press the Enter key"""
        try:
            pyautogui.press('enter')
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during enter!")
            raise

    def press_key(self, key: str):
        """
        Press a specific key

        Args:
            key: Key name (e.g., 'enter', 'space', 'esc')
        """
        try:
            pyautogui.press(key)
        except pyautogui.FailSafeException:
            print("[MacController] Fail-safe triggered during key press!")
            raise

    def reset_smoothing(self):
        """Reset smoothing state (useful when hand is lost then found)"""
        self.smooth_x = None
        self.smooth_y = None
