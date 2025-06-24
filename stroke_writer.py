def match_text_to_strokes(text_to_draw: str, strokes_json_path: str) -> list:
    import json
    import os
    from math import cos, sin, pi

    # Load handwriting strokes
    with open(strokes_json_path, "r") as f:
        strokes_dict = json.load(f)

    # Constants (image scale reference)
    scaleX = scaleY = 1  # Set to 1 since strokes are already normalized
    SCALE = 0.11
    CHAR_PADDING = 5 * SCALE * scaleX
    WORD_SPACING = 33 * SCALE * scaleX
    LINE_HEIGHT = 50 * SCALE * scaleY
    BED_WIDTH = 220
    BED_HEIGHT = 220
    MAX_LINE_WIDTH = 150
    x_offset = 10
    y_offset = 150

    descender_chars = ['p', 'q', 'y', 'g', 'j']
    reference_height = None
    descender_adjustment = None

    if 'a' in strokes_dict:
        a_strokes = [p for p in strokes_dict['a'] if p != ["UP", "UP", 0]]
        if a_strokes:
            a_min_y = min(p[1] for p in a_strokes)
            a_max_y = max(p[1] for p in a_strokes)
            reference_height = a_max_y - a_min_y

    if reference_height and 'p' in strokes_dict:
        p_strokes = [p for p in strokes_dict['p'] if p != ["UP", "UP", 0]]
        if p_strokes:
            p_min_y = min(p[1] for p in p_strokes)
            p_max_y = max(p[1] for p in p_strokes)
            p_height = p_max_y - p_min_y
            descender_adjustment = (p_height - reference_height) * 0.6

    output_paths = []
    cursor_x = x_offset
    cursor_y = y_offset

    for word in text_to_draw.split():
        word_width = 0
        for char in word:
            strokes = strokes_dict.get(char)
            if not strokes:
                continue
            min_x = min(p[0] for p in strokes if p != ["UP", "UP", 0])
            max_x = max(p[0] for p in strokes if p != ["UP", "UP", 0])
            word_width += (max_x - min_x) * SCALE + CHAR_PADDING

        if cursor_x + word_width > x_offset + MAX_LINE_WIDTH:
            cursor_x = x_offset
            cursor_y -= LINE_HEIGHT

        for char in word:
            if char == ".":
                dot_radius = 1.5 * SCALE
                num_segments = 16
                center_x = cursor_x + dot_radius
                center_y = cursor_y + dot_radius
                angle_step = 2 * pi / num_segments
                output_paths.append([center_x + dot_radius, center_y, 0])
                output_paths.append(["UP", "UP", 0])
                for i in range(1, num_segments + 1):
                    angle = i * angle_step
                    x = center_x + dot_radius * cos(angle)
                    y = center_y + dot_radius * sin(angle)
                    output_paths.append([x, y, 1])
                output_paths.append(["UP", "UP", 0])
                cursor_x += dot_radius * 2 + CHAR_PADDING
                continue

            strokes = strokes_dict.get(char)
            if not strokes:
                print(f"⚠️ No strokes for '{char}'")
                continue

            min_x = min(p[0] for p in strokes if p != ["UP", "UP", 0])
            max_x = max(p[0] for p in strokes if p != ["UP", "UP", 0])
            max_y = max(p[1] for p in strokes if p != ["UP", "UP", 0])
            char_width = (max_x - min_x) * SCALE

            y_adjustment = 0
            if char.islower() and char in descender_chars and descender_adjustment:
                y_adjustment = -descender_adjustment

            for point in strokes:
                if point == ["UP", "UP", 0]:
                    output_paths.append(["UP", "UP", 0])
                else:
                    x, y, pen = point
                    x -= min_x
                    flipped_y = (max_y - y) + y_adjustment
                    scaled_x = x * SCALE + cursor_x
                    scaled_y = flipped_y * SCALE + cursor_y
                    scaled_x = max(0, min(BED_WIDTH, scaled_x))
                    scaled_y = max(0, min(BED_HEIGHT, scaled_y))
                    output_paths.append([scaled_x, scaled_y, pen])
            output_paths.append(["UP", "UP", 0])
            cursor_x += char_width + CHAR_PADDING

        cursor_x += WORD_SPACING

    return output_paths

# Optional standalone use
if __name__ == "__main__":
    result = match_text_to_strokes(
        "Hi my name is guacamole and I like salsa.",
        "scribeAI/output/strokes.json"
    )
    with open("scribeAI/output/drawing_paths.json", "w") as f:
        json.dump(result, f, indent=2)
    print("✅ Stroke paths written.")
