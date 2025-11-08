"""Extract digits using spatial positioning."""
import pytesseract
from PIL import Image
import sys

if len(sys.argv) < 2:
    print("Usage: python test_spatial_ocr.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
image = Image.open(image_path)

print(f"\nSpatial OCR Analysis: {image_path}\n")

# Get detailed data with bounding boxes
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

# First, find the site number position
site_number_y = None
site_number_x = None

for i, text in enumerate(data['text']):
    if 'GDN' in text.upper() or ('248' in text and len(text) >= 7):
        site_number_y = data['top'][i]
        site_number_x = data['left'][i]
        print(f"Found site number '{text}' at position (x={site_number_x}, y={site_number_y})")
        break

if site_number_y is None:
    print("Could not find site number (GDN-248)")
else:
    # Now look for digits below the site number (within reasonable Y range)
    # Assuming artifact number is within 500 pixels below site number
    max_y = site_number_y + 500
    min_y = site_number_y + 50  # At least 50 pixels below

    print(f"\nLooking for digits between y={min_y} and y={max_y}:")
    print(f"{'Text':<15} {'Conf':<8} {'Position (x, y)':<20} {'Size (w x h)'}")
    print("-" * 70)

    digit_candidates = []

    for i, text in enumerate(data['text']):
        if text.strip() and text.isdigit():
            y = data['top'][i]
            x = data['left'][i]
            w = data['width'][i]
            h = data['height'][i]
            conf = int(data['conf'][i])

            if min_y <= y <= max_y and conf > 40:
                print(f"{text:<15} {conf:<8} ({x}, {y}){'':< 10} ({w} x {h})")
                digit_candidates.append({
                    'text': text,
                    'x': x,
                    'y': y,
                    'conf': conf
                })

    # Sort by Y position first, then X position
    digit_candidates.sort(key=lambda d: (d['y'], d['x']))

    # Group digits by similar Y position (within 20 pixels)
    if digit_candidates:
        print(f"\nGrouped by row:")
        rows = []
        current_row = [digit_candidates[0]]
        current_y = digit_candidates[0]['y']

        for digit in digit_candidates[1:]:
            if abs(digit['y'] - current_y) < 50:  # Same row
                current_row.append(digit)
            else:  # New row
                rows.append(current_row)
                current_row = [digit]
                current_y = digit['y']

        rows.append(current_row)  # Add last row

        for i, row in enumerate(rows, 1):
            row.sort(key=lambda d: d['x'])  # Sort by X within row
            digits = ''.join([d['text'] for d in row])
            print(f"  Row {i} (y≈{row[0]['y']}): {digits}")

            if len(digits) >= 5:
                print(f"    → Likely artifact number: {digits}")

print()
