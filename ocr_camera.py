import cv2
import pytesseract
import numpy as np
import time
import os
import re

# ============ Settings ============
INTERVAL_SEC = 0.5
OUTPUT_DIR = "ocr_regions"
PANEL_WIDTH = 420  # right-side text panel (set to 0 to disable)
MIN_BOX = 8        # ignore tiny accidental drags
MAX_REGIONS = 10   # cap regions
# ==================================

regions = []              # list[(x, y, w, h)]
drawing = False
start_pt = (0, 0)
preview_rect = None       # (x, y, w, h) while dragging
removing_mode = False
ocr_started = False
frame_shape = None        # (h, w)
latest_texts = []

def clip_rect(x, y, w, h, W, H):
    x = max(0, min(x, W-1))
    y = max(0, min(y, H-1))
    w = max(0, min(w, W - x))
    h = max(0, min(h, H - y))
    return x, y, w, h

def point_in_rect(px, py, rect):
    x, y, w, h = rect
    return (px >= x) and (px <= x + w) and (py >= y) and (py <= y + h)

def mouse_cb(event, x, y, flags, userdata):
    """Unified mouse handler: draw in Draw Mode, delete in Remove Mode."""
    global drawing, start_pt, preview_rect, regions, removing_mode, frame_shape

    if frame_shape is None:
        return
    H, W = frame_shape[:2]

    if removing_mode:
        # In remove mode, a single click inside a region removes it
        if event == cv2.EVENT_LBUTTONDOWN:
            for i, rect in enumerate(regions):
                if point_in_rect(x, y, rect):
                    removed = regions.pop(i)
                    print(f"Removed region R{i+1}: {removed}")
                    break
        return

    # Draw Mode
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_pt = (x, y)
        preview_rect = None
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        x0, y0 = start_pt
        rx, ry = min(x0, x), min(y0, y)
        rw, rh = abs(x - x0), abs(y - y0)
        rx, ry, rw, rh = clip_rect(rx, ry, rw, rh, W, H)
        preview_rect = (rx, ry, rw, rh)
    elif event == cv2.EVENT_LBUTTONUP and drawing:
        drawing = False
        x0, y0 = start_pt
        rx, ry = min(x0, x), min(y0, y)
        rw, rh = abs(x - x0), abs(y - y0)
        rx, ry, rw, rh = clip_rect(rx, ry, rw, rh, W, H)
        preview_rect = None
        if rw >= MIN_BOX and rh >= MIN_BOX:
            if len(regions) >= MAX_REGIONS:
                print(f"⚠️ Limit reached: only {MAX_REGIONS} regions allowed.")
            else:
                regions.append((rx, ry, rw, rh))
                print(f"Added region R{len(regions)}: {(rx, ry, rw, rh)}")
        else:
            print("Ignored tiny box; drag a larger area.")

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def cleanup_extra_region_files(num_regions):
    """Delete region_N.txt files with N > num_regions (keeps folder clean)."""
    patt = re.compile(r"region_(\d+)\.txt$")
    for name in os.listdir(OUTPUT_DIR):
        m = patt.match(name)
        if m:
            idx = int(m.group(1))
            if idx > num_regions:
                try:
                    os.remove(os.path.join(OUTPUT_DIR, name))
                except Exception:
                    pass

def draw_ui(display):
    """Draw boxes, labels, preview, and mode banner."""
    # regions
    for i, (x, y, w, h) in enumerate(regions):
        cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(display, f"R{i+1}", (x, max(0, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    # preview
    if preview_rect is not None:
        x, y, w, h = preview_rect
        cv2.rectangle(display, (x, y), (x + w, y + h), (255, 255, 0), 1)

    # mode banner
    banner = "REMOVE MODE: click a box to delete  (press 'r' to exit)" if removing_mode \
             else "DRAW MODE: drag to add box  |  'r' remove  's' start  'q' quit"
    color = (0, 0, 255) if removing_mode else (50, 200, 50)
    cv2.rectangle(display, (0, 0), (display.shape[1], 28), (0, 0, 0), -1)
    cv2.putText(display, banner, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

def run(camera_index=0):
    global frame_shape, ocr_started, removing_mode, latest_texts
    ensure_output_dir()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Camera {camera_index} not accessible.")
        return

    win = "OCR Multi-Region"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, mouse_cb)

    latest_texts = []
    last_ocr = 0.0

    print("Draw boxes; press 's' to start OCR, 'r' to toggle remove mode, 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame.")
            break

        frame_shape = frame.shape
        display = frame.copy()

        # Draw UI overlays
        draw_ui(display)

        # Optional right-side text panel
        if PANEL_WIDTH > 0:
            panel = np.ones((display.shape[0], PANEL_WIDTH, 3), dtype=np.uint8) * 255
        else:
            panel = None

        # OCR loop
        if ocr_started and regions and (time.time() - last_ocr >= INTERVAL_SEC):
            latest_texts = []
            for i, (x, y, w, h) in enumerate(regions):
                roi = frame[y:y+h, x:x+w]
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                text = pytesseract.image_to_string(gray).strip()
                latest_texts.append(text)

                # Write per-region file (overwrite, no timestamp)
                out_path = os.path.join(OUTPUT_DIR, f"region_{i+1}.txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)

            # remove stale files if region count decreased
            cleanup_extra_region_files(len(regions))
            last_ocr = time.time()

        # Render latest_texts on side panel
        if panel is not None:
            y0 = 36
            line_h = 22
            for i, text in enumerate(latest_texts):
                # Region header
                cv2.putText(panel, f"Region {i+1}:", (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2, cv2.LINE_AA)
                y0 += line_h
                # Text lines
                for line in (text.splitlines() or [""]):
                    if y0 > panel.shape[0] - 10:
                        break
                    cv2.putText(panel, line, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 1, cv2.LINE_AA)
                    y0 += line_h
                y0 += line_h  # extra gap between regions

            combined = np.hstack((display, panel))
        else:
            combined = display

        cv2.imshow(win, combined)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            if not regions:
                print("No regions selected yet.")
            else:
                ocr_started = True
                latest_texts = [""] * len(regions)
                print("OCR started.")
        elif key == ord('r'):
            removing_mode = not removing_mode
            state = "ON" if removing_mode else "OFF"
            print(f"Remove Mode: {state}")
        elif key == ord('c'):
            regions.clear()
            latest_texts = []
            print("Cleared all regions.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        cam_idx = int(input("Enter camera index (0=default): ").strip())
    except Exception:
        cam_idx = 0
    run(camera_index=cam_idx)
