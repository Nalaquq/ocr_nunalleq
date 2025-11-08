"""Simple OCR test without heavy preprocessing."""
import pytesseract
from PIL import Image
import sys

if len(sys.argv) < 2:
    print("Usage: python test_simple_ocr.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
print(f"\n=== Testing: {image_path} ===\n")

# Test 1: Raw OCR with minimal config
print("Test 1: Raw OCR")
image = Image.open(image_path)
text1 = pytesseract.image_to_string(image)
print(f"Result:\n{text1}\n")

# Test 2: Grayscale only
print("Test 2: Grayscale")
gray_image = image.convert('L')
text2 = pytesseract.image_to_string(gray_image)
print(f"Result:\n{text2}\n")

# Test 3: With digit focus
print("Test 3: Digit-focused config")
text3 = pytesseract.image_to_string(image, config='--psm 11')
print(f"Result:\n{text3}\n")

# Test 4: Get data to see confidence
print("Test 4: OCR with confidence data")
data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
for i, text in enumerate(data['text']):
    if text.strip() and int(data['conf'][i]) > 50:
        print(f"  '{text}' (conf: {data['conf'][i]})")
