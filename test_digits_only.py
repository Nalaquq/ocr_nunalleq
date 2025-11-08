"""Simple test with digits-only whitelist."""
import pytesseract
from PIL import Image
import sys

if len(sys.argv) < 2:
    print("Usage: python test_digits_only.py <image_path>")
    sys.exit(1)

image_path = sys.argv[1]
image = Image.open(image_path)

print(f"\nTesting: {image_path}\n")

# Test with digits-only whitelist
configs = [
    '--psm 11 -c tessedit_char_whitelist=0123456789',
    '--psm 6 -c tessedit_char_whitelist=0123456789',
    '--psm 12 -c tessedit_char_whitelist=0123456789',
]

for i, config in enumerate(configs, 1):
    print(f"Config {i}: {config}")
    text = pytesseract.image_to_string(image, config=config)
    # Extract just the digits
    digits = ''.join([c for c in text if c.isdigit()])
    print(f"  Digits found: {digits}")
    if len(digits) >= 5:
        print(f"  → Possible artifact number: {digits[:7]}")
    print()
