import os
import json
import numpy as np
from PIL import Image
from skimage.color import rgb2gray
from skimage.filters import threshold_otsu
from skimage.morphology import skeletonize

def extract_strokes(binary_img):
    """
    Given a binary image of one character, skeletonize it and extract stroke points,
    breaking into separate strokes if large jumps occur.
    """
    skel = skeletonize(binary_img)
    visited = np.zeros_like(skel, dtype=bool)
    height, width = skel.shape

    def neighbors(y, x):
        for j in [-1, 0, 1]:
            for i in [-1, 0, 1]:
                if i == 0 and j == 0:
                    continue
                ny, nx = y + j, x + i
                if 0 <= ny < height and 0 <= nx < width:
                    yield ny, nx

    strokes = []
    for y in range(height):
        for x in range(width):
            if skel[y, x] and not visited[y, x]:
                stack = [(y, x)]
                stroke = []
                last_point = None

                while stack:
                    cy, cx = stack.pop()
                    if visited[cy, cx]:
                        continue

                    visited[cy, cx] = True
                    curr_point = np.array([cx, cy])
                    if last_point is not None:
                        dist = np.linalg.norm(curr_point - last_point)
                        if dist > 15:  # Distance threshold to break rogue jump
                            stroke.append(["UP", "UP", 0])
                            strokes.extend(stroke)
                            stroke = []
                    stroke.append([int(cx), int(cy), 1])
                    last_point = curr_point

                    for ny, nx in neighbors(cy, cx):
                        if skel[ny, nx] and not visited[ny, nx]:
                            stack.append((ny, nx))

                if stroke:
                    stroke.append(["UP", "UP", 0])
                    strokes.extend(stroke)

    return strokes

def chaikin_smooth(stroke, iterations=2):
    """
    Applies Chaikin's corner-cutting algorithm to smooth a stroke.
    """
    for _ in range(iterations):
        new_stroke = []
        for i in range(len(stroke) - 1):
            p0 = np.array(stroke[i][:2])
            p1 = np.array(stroke[i+1][:2])
            Q = 0.75 * p0 + 0.25 * p1
            R = 0.25 * p0 + 0.75 * p1
            new_stroke.extend([[int(Q[0]), int(Q[1]), 1], [int(R[0]), int(R[1]), 1]])
        stroke = new_stroke
    return stroke

def generate_strokes_json(image_path: str, json_out_path: str) -> dict:
    """
    Extracts strokes from a labeled handwriting grid and saves them to json_out_path.
    Returns the dict with strokes.
    """
    # Load and scale image
    img_np = np.array(Image.open(image_path))
    height, width = img_np.shape[:2]
    ref_width, ref_height = 2092, 1584
    scaleX, scaleY = width / ref_width, height / ref_height

    # Grid and labels
    rows_per_section, cols = [3, 3, 2], 10
    labels = (list("abcdefghijklmnopqrstuvwxyz") + [""] * 4 +
              list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [""] * 4 +
              list("0123456789,.!?();") + [""] * 3)
    assert len(labels) == sum(rows_per_section) * cols

    start_x, start_y = int(172 * scaleX), int(330 * scaleY)
    box_w, box_h = int(172 * scaleX), int(118 * scaleY)
    row_spacing = int(128 * scaleY)
    margin_x, margin_y = 38, 16

    stroke_data = {}
    label_idx = 0
    curr_y = start_y

    for section_rows in rows_per_section:
        for r in range(section_rows):
            for c in range(cols):
                x1 = start_x + c * box_w
                y1 = curr_y + r * box_h
                x2 = x1 + box_w
                y2 = y1 + box_h

                # Crop character box with margin
                char_img = img_np[
                    y1 + margin_y : y2 - margin_y,
                    x1 + margin_x : x2 - margin_x
                ]

                # Convert to grayscale and threshold
                gray = rgb2gray(char_img)
                thresh = threshold_otsu(gray)
                binary = gray < thresh

                label = labels[label_idx]

                if label:
                    strokes = extract_strokes(binary)

                    smoothed = []
                    segment = []
                    for point in strokes:
                        if point[0] == "UP":
                            if len(segment) >= 2:
                                smoothed.extend(chaikin_smooth(segment))
                            segment = []
                            smoothed.append(point)
                        else:
                            segment.append(point)
                    if len(segment) >= 2:
                        smoothed.extend(chaikin_smooth(segment))

                    stroke_data[label] = smoothed

                label_idx += 1
        curr_y += section_rows * box_h + row_spacing

    os.makedirs(os.path.dirname(json_out_path), exist_ok=True)
    with open(json_out_path, "w") as f:
        json.dump(stroke_data, f, indent=2)

    print(f"✅ Smooth strokes.json generated with {len(stroke_data)} characters.")
    return stroke_data

if __name__ == "__main__":
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(BASE_DIR, "uploads", "handwriting.jpg")
    json_out = os.path.join(BASE_DIR, "output", "strokes.json")
    generate_strokes_json(img_path, json_out)
