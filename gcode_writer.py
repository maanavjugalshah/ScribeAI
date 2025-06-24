import json
import os
import math

def write_gcode(drawing_paths, output_path: str):
    """
    Converts stroke paths to G-code and saves to output_path (.gcode file).
    Accepts drawing_paths as a list of [x, y, pen] and writes the commands.
    """
    PEN_UP_Z = 2
    PEN_DOWN_Z = 0
    FEED_RATE = 40000
    DIST_THRESHOLD = 0.8

    gcode = [
        "; Start of G-code for handwriting plot",
        "G21 ; Set units to mm",
        "G28 ; Home all axes",
        "G90 ; Absolute positioning",
        f"G1 Z{PEN_UP_Z} F{FEED_RATE} ; Start with pen up",
    ]

    current_z = PEN_UP_Z
    prev_x, prev_y = None, None

    for point in drawing_paths:
        if point == ["UP", "UP", 0]:
            if current_z != PEN_UP_Z:
                gcode.append(f"G1 Z{PEN_UP_Z} F{FEED_RATE} ; Pen up")
                current_z = PEN_UP_Z
            prev_x, prev_y = None, None
            continue

        x, y, pen = point

        if prev_x is not None and prev_y is not None:
            dx, dy = x - prev_x, y - prev_y
            dist = math.hypot(dx, dy)
            if dist > DIST_THRESHOLD:
                if current_z != PEN_UP_Z:
                    gcode.append(f"G1 Z{PEN_UP_Z} F{FEED_RATE} ; Pen up")
                    current_z = PEN_UP_Z
                gcode.append(f"G0 X{x:.2f} Y{y:.2f}")
                gcode.append(f"G1 Z{PEN_DOWN_Z} F{FEED_RATE} ; Pen down")
                current_z = PEN_DOWN_Z
            elif current_z != PEN_DOWN_Z:
                gcode.append(f"G1 Z{PEN_DOWN_Z} F{FEED_RATE} ; Pen down")
                current_z = PEN_DOWN_Z
        else:
            gcode.append(f"G0 X{x:.2f} Y{y:.2f}")
            gcode.append(f"G1 Z{PEN_DOWN_Z} F{FEED_RATE} ; Pen down")
            current_z = PEN_DOWN_Z

        gcode.append(f"G1 X{x:.2f} Y{y:.2f} F{FEED_RATE}")
        prev_x, prev_y = x, y

    gcode += [
        f"G1 Z{PEN_UP_Z} F{FEED_RATE} ; Final pen up",
        "G1 X0 Y0 F3000 ; Return to origin",
        "M84 ; Disable motors",
        "; End of handwriting G-code"
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(gcode))
    print(f"✅ G-code saved to {output_path}")

# Optional test
if __name__ == "__main__":
    with open("scribeAI/output/drawing_paths.json", "r") as f:
        paths = json.load(f)
    write_gcode(paths, "scribeAI/output/final_output.gcode")
