Multi-Region OCR Camera App
===========================

This app lets you:
- Select up to 10 regions of the camera feed.
- Perform live OCR (Optical Character Recognition) on each region every 0.5 seconds.
- Save each region’s text into its own .txt file inside an ocr_regions/ folder.
- Remove or re-draw regions anytime.
- See live OCR results in a side panel.

Requirements
------------
- Python 3.8+
- Tesseract OCR
- Webcam (built-in or USB)

Installation
------------

1. Clone the repository:
   git clone https://github.com/procoder26/ocr-camera.git
   cd ocr-camera

2. Install dependencies:

macOS (requires Homebrew):
   brew install python
   brew install tesseract

Windows:
   - Install Python 3 from python.org
   - Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki

3. Python dependencies:

Option A (recommended, with virtual environment):
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   pip install opencv-python pytesseract numpy

Option B (global install):
   pip install opencv-python pytesseract numpy

Running the App
---------------
Run from inside your project folder:
   python ocr_camera.py

If using a virtual environment, make sure it is activated first.

You will be prompted for the camera index:
   Enter camera index (0=default):
   Use 0 for default, or 1/2/etc. for external or virtual cameras.

Controls
--------
- Draw Mode (default): Click + drag to add a region (max 10).
- Remove Mode: Press r, then click inside a box to delete it. Press r again to exit.
- Start OCR: Press s.
- Clear All Regions: Press c.
- Quit: Press q.

Output
------
OCR results are stored in:
   ocr_regions/region_1.txt
   ocr_regions/region_2.txt
   ...

Each file is overwritten every cycle.
If you remove a region, extra files are deleted automatically.

Troubleshooting
---------------
- macOS camera access:
  System Settings → Privacy & Security → Camera → allow Terminal (or whatever terminal your using).

- Windows Tesseract path issue:
  If you see TesseractNotFoundError, add Tesseract to PATH:
     setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"

- ModuleNotFoundError: No module named 'cv2':
  Install OpenCV:
     pip install opencv-python

- Too many regions:
  Max is 10. Remove one before adding another.
