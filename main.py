#!/usr/bin/env python3
"""
Precrime Interface - Main Entry Point
A "Minority Report" style gesture control interface using MediaPipe and OpenCV
"""

import cv2
import sys
import time
import traceback
from typing import Optional

import config
from hand_detector import HandDetector
from gesture_engine import GestureEngine
from holo_hud import HoloHUD
from mac_controller import MacController


class PrecrimeInterface:
    """
    Main application class for the Precrime Interface
    """

    def __init__(self):
        """Initialize all components"""
        print("=" * 60)
        print("PRECRIME INTERFACE - Gesture Control System")
        print("=" * 60)
        print("\nInitializing components...")

        # Initialize camera
        print("  [1/4] Initializing camera...")
        self.camera = cv2.VideoCapture(config.CAMERA_INDEX)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self.camera.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

        if not self.camera.isOpened():
            raise RuntimeError("Failed to open camera!")

        # Get actual camera dimensions
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"      Camera opened: {actual_width}x{actual_height}")

        # Initialize hand detector
        print("  [2/4] Initializing hand detector...")
        self.detector = HandDetector()
        print("      Hand detector ready")

        # Initialize gesture engine
        print("  [3/4] Initializing gesture engine...")
        self.gesture_engine = GestureEngine(self.detector)
        print("      Gesture engine ready")

        # Initialize HUD
        print("  [4/4] Initializing visual HUD...")
        self.hud = HoloHUD(actual_width, actual_height)
        print("      HUD ready")

        # Initialize controller
        print("  [5/5] Initializing system controller...")
        self.controller = MacController(actual_width, actual_height)
        print("      Controller ready")

        # State
        self.running = False
        self.prev_hand_count = 0

        print("\n" + "=" * 60)
        print("INITIALIZATION COMPLETE")
        print("=" * 60)
        print("\nControls:")
        print("  - Point with index finger to move cursor")
        print("  - Pinch (thumb + index) to click")
        print("  - Open hand + move vertically to scroll")
        print("  - Use both hands to zoom (move apart/together)")
        print("  - Make a fist for 1 second to pause/resume")
        print("  - Push hand forward quickly for Enter key")
        print("  - Press 'q' to quit")
        print("\nStarting in SAFE MODE (make fist to activate)...")
        print("=" * 60 + "\n")

    def run(self):
        """Main application loop"""
        self.running = True

        try:
            while self.running:
                # Read frame from camera
                success, frame = self.camera.read()

                if not success:
                    print("[ERROR] Failed to read frame from camera")
                    break

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)

                # Detect hands
                hands = self.detector.find_hands(frame, draw=False)

                # Analyze gestures
                gesture_state = self.gesture_engine.analyze(hands)

                # Handle hand tracking loss/recovery
                current_hand_count = len(hands)
                if current_hand_count == 0 and self.prev_hand_count > 0:
                    # Hand lost - reset smoothing
                    self.controller.reset_smoothing()
                self.prev_hand_count = current_hand_count

                # Execute gestures (only if not paused)
                if not gesture_state.is_paused:
                    self._execute_gestures(gesture_state, hands)

                # Render HUD
                frame = self.hud.render(frame, hands, gesture_state)

                # Display frame
                cv2.imshow('Precrime Interface', frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\n[INFO] Quit requested by user")
                    break

        except pyautogui.FailSafeException:
            print("\n[SAFETY] PyAutoGUI fail-safe triggered!")
            print("         Mouse moved to corner. Shutting down safely.")

        except KeyboardInterrupt:
            print("\n[INFO] Keyboard interrupt received")

        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            traceback.print_exc()

        finally:
            self._cleanup()

    def _execute_gestures(self, gesture_state, hands):
        """
        Execute system actions based on detected gestures

        Args:
            gesture_state: Current GestureState
            hands: List of detected hands
        """
        try:
            # Move cursor
            if gesture_state.cursor_position:
                cam_x, cam_y = gesture_state.cursor_position
                self.controller.move_cursor(cam_x, cam_y)

            # Click
            if gesture_state.is_clicking:
                self.controller.click()

            # Scroll
            if gesture_state.is_scrolling and hands:
                scroll_amount = self.gesture_engine.get_scroll_amount(hands[0])
                if scroll_amount != 0:
                    self.controller.scroll(scroll_amount)

            # Zoom
            if gesture_state.is_zooming:
                if gesture_state.zoom_direction == 'out':
                    self.controller.zoom_in()
                elif gesture_state.zoom_direction == 'in':
                    self.controller.zoom_out()

            # Air push (Enter)
            if gesture_state.air_push_detected:
                self.controller.press_enter()

        except pyautogui.FailSafeException:
            raise  # Re-raise fail-safe exception

        except Exception as e:
            print(f"[WARNING] Error executing gesture: {e}")

    def _cleanup(self):
        """Clean up resources"""
        print("\nCleaning up...")

        if hasattr(self, 'camera'):
            self.camera.release()
            print("  Camera released")

        if hasattr(self, 'detector'):
            self.detector.close()
            print("  Detector closed")

        cv2.destroyAllWindows()
        print("  Windows closed")

        print("\nShutdown complete. Goodbye!")


def main():
    """Entry point"""
    try:
        app = PrecrimeInterface()
        app.run()
    except Exception as e:
        print(f"\n[FATAL ERROR] Failed to initialize: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
