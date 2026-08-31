"""
Scoreboard Data Extraction from Video (v2)
---------------------------------------
Pipeline: Frame Extraction -> ROI Cropping -> Color-mask Preprocessing ->
          Split Name/Score OCR -> Parsing -> Contiguous-run Grouping -> Save

Requirements:
    pip install opencv-python pytesseract numpy

Also requires the Tesseract OCR engine installed separately:
    Windows: https://github.com/UB-Mannheim/tesseract/wiki
    Mac:     brew install tesseract
    Linux:   sudo apt install tesseract-ocr
"""

import cv2
import json
import re
import pytesseract

# ---------------------------------------------------------------------
# If Tesseract isn't on your PATH (common on Windows), set this to your
# actual install path:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# ---------------------------------------------------------------------


def extract_frames(video_path, sample_rate=1):
    """Extract frames from video at a given sample rate (frames per second)."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(1, int(fps / sample_rate))

    frames = []
    idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % frame_interval == 0:
            frames.append(frame)
        idx += 1

    cap.release()
    print(f"Extracted {len(frames)} frames from {video_path} (fps={fps:.1f})")
    return frames


def get_roi_fixed(frame, x, y, w, h):
    """Crop a fixed region of interest (the scoreboard) from a frame."""
    return frame[y:y + h, x:x + w]


def preprocess_roi(roi):
    """
    Isolate bright text (yellow/white digits & letters) from a solid
    blue scoreboard background, then binarize + upscale for OCR.
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Background blue sits around H=113 on this scoreboard — mask it OUT
    # instead of hunting for the exact text color (more robust).
    blue_mask = cv2.inRange(hsv, (95, 50, 50), (130, 255, 255))
    not_blue = cv2.bitwise_not(blue_mask)

    # Keep only bright pixels among the non-blue area (removes faint noise)
    v_channel = hsv[:, :, 2]
    bright_mask = cv2.inRange(v_channel, 150, 255)

    text_mask = cv2.bitwise_and(not_blue, bright_mask)

    # Clean up small speckles
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    cleaned = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel)

    # Tesseract prefers dark text on light background — invert
    inverted = cv2.bitwise_not(cleaned)

    # Upscale for better OCR on small text
    resized = cv2.resize(inverted, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

    return resized


def extract_text(image, mode="name"):
    """
    Run OCR on a single-line image region.
    mode="name"  -> allow letters (player names)
    mode="score" -> digits/symbols only (bowling: strike X, spare /, dash -)
    """
    if mode == "score":
        config = "--psm 7 -c tessedit_char_whitelist=0123456789/-X"
    else:
        config = "--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()


def parse_scoreboard(name_text, score_text):
    """Extract structured fields from the separately-OCR'd name/score strings."""
    scores = re.findall(r"\d+", score_text)
    return {
        "name_raw": name_text,
        "score_raw": score_text,
        "scores": scores,
    }


def group_contiguous_runs(results, key="name_raw", min_run_length=2):
    """
    Group consecutive frames that share the same OCR'd name into single
    records, instead of emitting one noisy row per frame. This matches
    how a real scoreboard behaves: one name stays on screen for a run
    of frames, then changes when the next player is up.

    Frames with empty/blank OCR text are skipped (treated as transitions).
    min_run_length filters out one-off misreads that never repeated.
    """
    runs = []
    current_value = None
    current_frames = []
    current_scores = []

    def flush():
        if current_value and len(current_frames) >= min_run_length:
            runs.append({
                "name": current_value,
                "frames": current_frames[:],
                "scores_seen": sorted(set(current_scores)),
            })

    for r in results:
        value = r[key].strip()
        if not value:
            # blank frame - treat as a gap, flush current run
            flush()
            current_value = None
            current_frames = []
            current_scores = []
            continue

        if value == current_value:
            current_frames.append(r["frame_index"])
            current_scores.extend(r["scores"])
        else:
            flush()
            current_value = value
            current_frames = [r["frame_index"]]
            current_scores = list(r["scores"])

    flush()  # capture the last run
    return runs


def save_results(results, output_path="scoreboard_log.json"):
    """Save structured results to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved results to {output_path}")


def save_debug_frame(video_path, out_path="sample_frame.png"):
    """Grab the first frame of the video so you can find ROI coordinates."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(out_path, frame)
        print(f"Saved sample frame to {out_path} — open it to find scoreboard coordinates.")
    cap.release()


if __name__ == "__main__":
    # ------------------------------------------------------------------
    # CONFIG — edit these values for your video and scoreboard position
    # ------------------------------------------------------------------
    VIDEO_PATH = "match.mp4"
    SAMPLE_RATE = 1
    ROI_X, ROI_Y = 50, 20
    ROI_W, ROI_H = 400, 100
    NAME_SPLIT_RATIO = 0.55        # top 55% of ROI = name row, rest = score row
    OUTPUT_JSON = "scoreboard_log.json"          # raw per-frame log
    OUTPUT_SUMMARY_JSON = "scoreboard_summary.json"  # grouped-by-player log

    # Step 0 (run once): uncomment to grab a sample frame and find ROI coords
    # save_debug_frame(VIDEO_PATH)

    # Step 1: extract frames
    frames = extract_frames(VIDEO_PATH, sample_rate=SAMPLE_RATE)

    # Step 2-5: crop, preprocess, OCR (split name/score), parse each frame
    results = []
    for i, frame in enumerate(frames):
        roi = get_roi_fixed(frame, ROI_X, ROI_Y, ROI_W, ROI_H)
        processed = preprocess_roi(roi)

        h = processed.shape[0]
        split_row = int(h * NAME_SPLIT_RATIO)
        name_region = processed[0:split_row, :]
        score_region = processed[split_row:, :]

        name_text = extract_text(name_region, mode="name")
        score_text = extract_text(score_region, mode="score")

        parsed = parse_scoreboard(name_text, score_text)
        parsed["frame_index"] = i
        results.append(parsed)
        print(f"Frame {i}: name='{name_text}' score='{score_text}'")

    # Step 6: save the raw per-frame log (useful for debugging)
    save_results(results, OUTPUT_JSON)

    # Step 7: group into contiguous per-player runs — the clean deliverable
    summary = group_contiguous_runs(results, key="name_raw", min_run_length=2)
    save_results(summary, OUTPUT_SUMMARY_JSON)

    print("\n=== Summary ===")
    for run in summary:
        print(run)