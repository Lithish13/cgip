#!/usr/bin/env python3
"""
Python OpenCV + MediaPipe Gesture-Based Calculator (CGIP Project)
-----------------------------------------------------------------
Controls:
  - Move your Index Finger (Landmark 8) to hover over virtual calculator buttons.
  - Pinch your Thumb (Landmark 4) & Index Finger (Landmark 8) together to press a button.
  - Press 'c' on keyboard to clear, or 'q' / ESC to quit.

Requirements:
  pip install opencv-python mediapipe numpy
"""

import math
import time
import cv2
import numpy as np

try:
    import mediapipe as mp
except ImportError:
    raise SystemExit("Please install mediapipe and opencv-python: pip install opencv-python mediapipe numpy")


class Button:
    def __init__(self, pos, width, height, value):
        self.pos = pos  # (x, y)
        self.width = width
        self.height = height
        self.value = value

    def draw(self, img, hovered=False, clicked=False):
        x, y = self.pos
        w, h = self.width, self.height

        # Color scheme (BGR format)
        if clicked:
            bg_color = (254, 242, 0)      # Bright Cyan flash
            text_color = (15, 15, 15)
        elif hovered:
            bg_color = (75, 55, 35)       # Highlighted dark slate
            text_color = (254, 242, 0)
        else:
            bg_color = (35, 25, 18) if self.value not in ["=", "AC"] else (55, 30, 45)
            text_color = (240, 240, 240)

        # Draw button box with semi-transparent overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), bg_color, cv2.FILLED)
        cv2.addWeighted(overlay, 0.82, img, 0.18, 0, img)

        # Border
        border_color = (254, 242, 0) if hovered or clicked else (120, 100, 80)
        cv2.rectangle(img, (x, y), (x + w, y + h), border_color, 2)

        # Centered label
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.9 if len(self.value) == 1 else 0.75
        thickness = 2
        (tw, th), _ = cv2.getTextSize(self.value, font, scale, thickness)
        tx = x + (w - tw) // 2
        ty = y + (h + th) // 2
        cv2.putText(img, self.value, (tx, ty), font, scale, text_color, thickness, cv2.LINE_AA)

    def is_inside(self, cx, cy):
        x, y = self.pos
        return x <= cx <= x + self.width and y <= cy <= y + self.height


def safe_eval(expr: str) -> str:
    try:
        clean = expr.replace("×", "*").replace("÷", "/")
        allowed = set("0123456789+-*/.%() ")
        if not clean or any(ch not in allowed for ch in clean):
            return "Error"
        result = eval(clean, {"__builtins__": None}, {})
        if isinstance(result, float):
            return str(round(result, 6)).rstrip("0").rstrip(".") or "0"
        return str(result)
    except Exception:
        return "Error"


def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    # Calculator keypad layout (4x5 grid on the right side of the screen)
    keys = [
        ["AC", "DEL", "%", "÷"],
        ["7",  "8",   "9", "×"],
        ["4",  "5",   "6", "-"],
        ["1",  "2",   "3", "+"],
        ["0",  ".",   "(", ")"],
    ]

    start_x, start_y = 760, 170
    btn_w, btn_h, gap = 95, 75, 12
    buttons = []
    for r, row in enumerate(keys):
        for c, val in enumerate(row):
            bx = start_x + c * (btn_w + gap)
            by = start_y + r * (btn_h + gap)
            buttons.append(Button((bx, by), btn_w, btn_h, val))

    # Full-width '=' button at the bottom
    eq_y = start_y + 5 * (btn_h + gap)
    total_w = 4 * btn_w + 3 * gap
    buttons.append(Button((start_x, eq_y), total_w, 65, "="))

    expression = ""
    last_click_time = 0
    click_cooldown = 0.55  # seconds

    print("[*] Gesture Calculator running. Pinch Thumb + Index finger over a button to click. Press 'q' to exit.")

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Draw calculator display screen
        disp_x1, disp_y1 = start_x, 60
        disp_x2, disp_y2 = start_x + total_w, 150
        cv2.rectangle(frame, (disp_x1, disp_y1), (disp_x2, disp_y2), (20, 15, 10), cv2.FILLED)
        cv2.rectangle(frame, (disp_x1, disp_y1), (disp_x2, disp_y2), (254, 242, 0), 2)

        shown_text = expression[-18:] if expression else "0"
        cv2.putText(
            frame, shown_text, (disp_x1 + 15, disp_y2 - 28),
            cv2.FONT_HERSHEY_SIMPLEX, 1.15, (255, 255, 255), 2, cv2.LINE_AA
        )

        cursor_pos = None
        is_pinching = False

        if results.multi_hand_landmarks:
            hand_lms = results.multi_hand_landmarks[0]
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)

            # Index tip (8) and Thumb tip (4)
            x8, y8 = int(hand_lms.landmark[8].x * w), int(hand_lms.landmark[8].y * h)
            x4, y4 = int(hand_lms.landmark[4].x * w), int(hand_lms.landmark[4].y * h)

            cursor_pos = (x8, y8)
            pinch_dist = math.hypot(x8 - x4, y8 - y4)
            is_pinching = pinch_dist < 42

            # Draw pinch line and cursor reticle
            mid_x, mid_y = (x8 + x4) // 2, (y8 + y4) // 2
            cv2.line(frame, (x8, y8), (x4, y4), (254, 242, 0), 2)
            cv2.circle(frame, (x8, y8), 10, (0, 255, 128) if is_pinching else (254, 242, 0), cv2.FILLED)
            if is_pinching:
                cv2.circle(frame, (mid_x, mid_y), 14, (0, 230, 118), 3)

        # Render buttons & check interactions
        now = time.time()
        for btn in buttons:
            hovered = cursor_pos is not None and btn.is_inside(*cursor_pos)
            clicked = False

            if hovered and is_pinching and (now - last_click_time) > click_cooldown:
                clicked = True
                last_click_time = now
                val = btn.value
                if val == "AC":
                    expression = ""
                elif val == "DEL":
                    expression = expression[:-1]
                elif val == "=":
                    expression = safe_eval(expression)
                else:
                    if expression == "Error":
                        expression = ""
                    expression += val

            btn.draw(frame, hovered=hovered, clicked=clicked)

        # Header HUD
        cv2.putText(
            frame, "CGIP Gesture Calculator | Pinch (Thumb+Index) to Click | 'Q' to Quit",
            (25, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 230, 240), 2, cv2.LINE_AA
        )

        cv2.imshow("CGIP - Python Gesture Calculator", frame)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        elif key == ord("c"):
            expression = ""

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
