Scoreboard OCR – Computer Vision

Overview

This project extracts scoreboard information from a video using Computer Vision and Optical Character Recognition (OCR).

The input video is processed frame by frame. The scoreboard region is cropped, preprocessed, and passed to OCR. The extracted text is then cleaned and saved as structured output.

Input

Place the input video in the project folder and update the video path in scoreboard_ocr.py.

Example:

scoreboard-ocr/
├── scoreboard_ocr.py
├── requirements.txt
├── README.md
├── .gitignore
└── bowling_scoreboard.mp4

Technologies

Python

OpenCV

NumPy

Pytesseract

Tesseract OCR

Installation

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd scoreboard-ocr

2. Create a virtual environment

Windows:

py -m venv venv
venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Install Tesseract OCR

Install Tesseract OCR separately on your system.

Verify the installation:

tesseract --version

If Tesseract is not detected automatically on Windows, set its path in scoreboard_ocr.py:

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

How to Run

Open the project in VS Code and activate the virtual environment.

Run:

python scoreboard_ocr.py

If python is not recognized on Windows, use:

py scoreboard_ocr.py

Processing Pipeline

Input Video
     ↓
Frame Extraction
     ↓
Scoreboard Region (ROI)
     ↓
Image Preprocessing
     ↓
OCR
     ↓
Text Cleaning / Parsing
     ↓
Scoreboard Data Output

1. Frame Extraction

Frames are sampled from the input video instead of unnecessarily processing every frame.

2. Scoreboard ROI

The scoreboard area is cropped from each selected frame using the configured region of interest (ROI).

3. Image Preprocessing

The cropped scoreboard is processed to improve OCR quality. The processing can include:

Grayscale conversion

Contrast enhancement

Thresholding

Noise reduction

Resizing

4. OCR

Tesseract OCR is used to recognize the scoreboard text and numbers.

5. Parsing

The OCR result is cleaned and relevant scoreboard values are extracted.

Output

The program produces the extracted scoreboard information according to the output files configured in scoreboard_ocr.py.

Typical output can include:

scoreboard_log.json

Example:

{
    "frame": 30,
    "time_seconds": 1.0,
    "score": "87/3"
}

The exact fields depend on the scoreboard format and the implementation in scoreboard_ocr.py.

Debugging

If the OCR result is incorrect:

Check the scoreboard ROI coordinates.

Verify that the cropped region contains only the scoreboard.

Inspect the preprocessed image.

Adjust the OCR configuration.

Test different thresholding or preprocessing settings.

Repository Structure

scoreboard-ocr/
├── scoreboard_ocr.py
├── requirements.txt
├── README.md
└── .gitignore

Requirements

Python 3.8 or later

OpenCV

NumPy

Pytesseract

Tesseract OCR

Input scoreboard video

Notes

The accuracy of OCR depends on the video resolution, scoreboard size, font, image quality, motion blur, and ROI selection.

For the provided video, the ROI and OCR settings should be tuned to the actual scoreboard layout.

Assignment Deliverables

The project is intended to provide:

A GitHub repository containing the source code and README.

A demonstration showing the input video, code execution, scoreboard detection/extraction, and final data.

Documentation containing screenshots of the input frame, running code, detected scoreboard, and extracted output.

Author

Sunandagokhe