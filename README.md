# Precrime Interface

A "Minority Report" style gesture control interface for macOS using Python and MediaPipe.

## Features

- **Hand Tracking**: Real-time hand detection and landmark tracking using MediaPipe
- **Gesture Control**:
  - Cursor movement with index finger
  - Left click with pinch gesture
  - Scroll mode with "high five" pose
  - Two-hand zoom gestures
  - Safety pause with fist gesture
  - Air push (Z-axis) for Enter key
- **Sci-Fi HUD**: Cyan/teal visual overlay inspired by Minority Report
- **Smooth Control**: Exponential Moving Average smoothing for stable cursor movement

## Requirements

- Python 3.10+
- macOS (optimized for macOS, may work on other platforms)
- Webcam (720p recommended)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the gesture control interface
python main.py
```

## Controls

- **Move Cursor**: Point with index finger
- **Click**: Pinch thumb and index finger together
- **Scroll**: Open hand (all fingers up) and move vertically
- **Zoom In/Out**: Use both hands, move index fingers apart/together
- **Pause/Resume**: Close fist for 1 second
- **Enter Key**: Push hand forward quickly (Z-axis)
- **Exit**: Press 'q' or move mouse to top-left corner (fail-safe)

## Configuration

Edit `config.py` to adjust:
- Camera resolution and FPS
- Detection confidence thresholds
- Smoothing factor
- Gesture sensitivity

## Architecture

- `hand_detector.py`: MediaPipe wrapper for hand detection
- `gesture_engine.py`: Gesture recognition and interpretation
- `holo_hud.py`: Visual overlay rendering
- `mac_controller.py`: System control interface
- `config.py`: Configuration constants
- `main.py`: Entry point

## Safety Features

- Fail-safe corner (top-left) triggers abort
- Debouncing to prevent accidental double-clicks
- Active/pause toggle for safety
- Smooth movement to prevent jerky control

## License

MIT License

## Credits

Built with MediaPipe, OpenCV, and PyAutoGUI.
