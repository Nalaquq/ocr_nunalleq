"""Detailed OCR diagnostic with bounding boxes."""
import pytesseract
from PIL import Image
import sys

if len(sys.argv) < 2:
    print("Usage: python test_detailed_ocr.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
print(f"\n=== Detailed OCR Analysis: {image_path} ===\n")

image = Image.open(image_path)

# Get detailed data with bounding boxes and confidence
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

print("All detected text with confidence > 30:")
print(f"{'Text':<20} {'Confidence':<12} {'Position (x,y)'}")
print("-" * 60)

for i, text in enumerate(data['text']):
    conf = int(data['conf'][i])
    if text.strip() and conf > 30:
        x, y = data['left'][i], data['top'][i]
        print(f"{text:<20} {conf:<12} ({x}, {y})")

print("\n" + "="*60)
print("Full text extraction:")
print("="*60)
text = pytesseract.image_to_string(image)
print(text)

print("\n" + "="*60)
print("Looking for digit patterns:")
print("="*60)

# Find all individual digits
import re
all_text = ' '.join([t for t in data['text'] if t.strip()])
digits = re.findall(r'\d', all_text)
print(f"Individual digits found: {digits}")
print(f"Combined: {''.join(digits)}")

# Find digit sequences
digit_sequences = re.findall(r'\d+', all_text)
print(f"\nDigit sequences found: {digit_sequences}")
