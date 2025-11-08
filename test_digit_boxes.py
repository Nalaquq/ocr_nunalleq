"""Test different OCR configurations for digit boxes."""
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import sys
import cv2
import numpy as np

if len(sys.argv) < 2:
    print("Usage: python test_digit_boxes.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
print(f"\n=== Testing Digit Box Detection: {image_path} ===\n")

image = Image.open(image_path)

# Test different PSM modes
psm_modes = {
    3: "Fully automatic page segmentation",
    6: "Assume a single uniform block of text",
    7: "Treat the image as a single text line",
    11: "Sparse text. Find as much text as possible",
    12: "Sparse text with OSD (Orientation and Script Detection)",
    13: "Raw line. Treat as single text line, bypass hacks"
}

for psm, description in psm_modes.items():
    print(f"\nPSM {psm}: {description}")
    config = f'--oem 3 --psm {psm}'
    try:
        text = pytesseract.image_to_string(image, config=config)
        # Only show non-empty results
        if text.strip():
            lines = [line for line in text.split('\n') if line.strip()]
            for line in lines[:5]:  # Show first 5 lines
                print(f"  {line}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*60)
print("Testing with preprocessing:")
print("="*60)

# Convert to OpenCV
img_cv = cv2.imread(image_path)
gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

# Try different preprocessing approaches
print("\n1. Otsu's thresholding:")
_, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
thresh1_pil = Image.fromarray(thresh1)
text1 = pytesseract.image_to_string(thresh1_pil, config='--psm 11')
if text1.strip():
    print(f"  {[line for line in text1.split() if line.strip()][:10]}")

print("\n2. Adaptive thresholding (Mean):")
thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
thresh2_pil = Image.fromarray(thresh2)
text2 = pytesseract.image_to_string(thresh2_pil, config='--psm 11')
if text2.strip():
    print(f"  {[line for line in text2.split() if line.strip()][:10]}")

print("\n3. Inverted (white on black):")
inverted = cv2.bitwise_not(thresh1)
inverted_pil = Image.fromarray(inverted)
text3 = pytesseract.image_to_string(inverted_pil, config='--psm 11')
if text3.strip():
    print(f"  {[line for line in text3.split() if line.strip()][:10]}")

print("\n4. Digits only mode:")
config_digits = '--psm 11 -c tessedit_char_whitelist=0123456789'
text4 = pytesseract.image_to_string(image, config=config_digits)
if text4.strip():
    print(f"  {[line for line in text4.split() if line.strip()][:10]}")

print("\n5. Digits only with thresholding:")
text5 = pytesseract.image_to_string(thresh1_pil, config=config_digits)
if text5.strip():
    print(f"  {text5.strip()}")
