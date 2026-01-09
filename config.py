"""
Configuration Constants for Precrime Interface
Adjust these values to tune the gesture control system
"""

# ============================================================================
# CAMERA SETTINGS
# ============================================================================
CAMERA_INDEX = 0  # Default camera (0 = built-in webcam)
CAMERA_WIDTH = 1280  # HD resolution
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# ============================================================================
# MEDIAPIPE DETECTION SETTINGS
# ============================================================================
MAX_NUM_HANDS = 2  # Maximum number of hands to detect
MIN_DETECTION_CONFIDENCE = 0.7  # Minimum confidence for hand detection
MIN_TRACKING_CONFIDENCE = 0.5  # Minimum confidence for hand tracking

# ============================================================================
# SMOOTHING SETTINGS
# ============================================================================
SMOOTHING_ALPHA = 0.5  # EMA smoothing factor (0-1)
# Higher = more responsive but jittery
# Lower = smoother but more lag

# ============================================================================
# GESTURE DETECTION THRESHOLDS
# ============================================================================
# Click Detection (Pinch)
PINCH_THRESHOLD = 30  # pixels - distance between thumb and index for click
CLICK_DEBOUNCE_TIME = 0.3  # seconds - minimum time between clicks

# Fist Detection (Pause)
FIST_THRESHOLD = 0.3  # Normalized distance threshold for closed fist
FIST_DURATION = 1.0  # seconds - how long to hold fist to toggle pause

# Zoom Detection (Two hands)
ZOOM_SENSITIVITY = 50  # pixels - minimum distance change to trigger zoom
ZOOM_DEBOUNCE_TIME = 0.2  # seconds - minimum time between zoom actions

# Air Push Detection (Z-axis)
AIR_PUSH_AREA_THRESHOLD = 0.2  # 20% increase in hand bounding box area
AIR_PUSH_TIME_WINDOW = 0.2  # seconds - time window to detect push

# Scroll Detection
SCROLL_SENSITIVITY = 2  # pixels per movement unit
SCROLL_THRESHOLD = 10  # minimum vertical movement to trigger scroll

# ============================================================================
# SCREEN MAPPING SETTINGS
# ============================================================================
# Use central 70% of camera frame to map to full screen
# This prevents users from stretching arms too far
INTERACTION_REGION_X = 0.15  # 15% margin on left
INTERACTION_REGION_Y = 0.15  # 15% margin on top
INTERACTION_REGION_WIDTH = 0.70  # 70% of frame width
INTERACTION_REGION_HEIGHT = 0.70  # 70% of frame height

# ============================================================================
# VISUAL HUD SETTINGS
# ============================================================================
# Colors (BGR format for OpenCV)
HUD_COLOR_PRIMARY = (255, 255, 0)  # Cyan (#00FFFF)
HUD_COLOR_ACTIVE = (0, 255, 0)  # Green
HUD_COLOR_CLICKING = (255, 0, 255)  # Magenta
HUD_COLOR_TEXT = (255, 255, 255)  # White

# Transparency
HUD_LINE_ALPHA = 0.6  # Transparency for connection lines
HUD_CIRCLE_ALPHA = 0.8  # Transparency for fingertip circles

# Sizes
HUD_LINE_THICKNESS = 2
HUD_CIRCLE_RADIUS_BASE = 8
HUD_CIRCLE_RADIUS_DEPTH_SCALE = 5  # Scale factor for depth-based radius

# Text
HUD_FONT = 1  # cv2.FONT_HERSHEY_SIMPLEX
HUD_FONT_SCALE = 1.0
HUD_FONT_THICKNESS = 2

# ============================================================================
# SAFETY SETTINGS
# ============================================================================
FAILSAFE_ENABLED = True  # PyAutoGUI fail-safe (top-left corner)
PAUSE_KEY = 'q'  # Keyboard key to quit application

# ============================================================================
# LANDMARK IDS (MediaPipe Hand Landmarks)
# ============================================================================
# Reference: https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
LANDMARK_WRIST = 0
LANDMARK_THUMB_TIP = 4
LANDMARK_INDEX_TIP = 8
LANDMARK_MIDDLE_TIP = 12
LANDMARK_RING_TIP = 16
LANDMARK_PINKY_TIP = 20

# All fingertips
FINGERTIP_IDS = [4, 8, 12, 16, 20]

# Hand connections for drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),  # Index
    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (5, 9), (9, 13), (13, 17)  # Palm
]
