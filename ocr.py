import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re
import os

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

class NoTextFoundError(Exception):
    """Exception raised when no text is found in an image."""
    pass

def preprocess_image(image):
    """
    Preprocesses the image to enhance text recognition.

    Args:
        image (PIL.Image.Image): The input image.

    Returns:
        PIL.Image.Image: The preprocessed image.
    """
    # Convert image to grayscale
    image = image.convert('L')
    # Enhance the contrast
    image = ImageEnhance.Contrast(image).enhance(2)
    # Resize the image to double the size for better recognition
    width, height = image.size
    image = image.resize((width * 2, height * 2), Image.BILINEAR)
    # Apply a slight blur to smooth out the edges
    image = image.filter(ImageFilter.MedianFilter())
    # Apply a threshold to get a binary image
    image = image.point(lambda x: 0 if x < 140 else 255, '1')
    return image

def extract_text_and_numbers(image_path):
    """
    Extracts any text and numbers from an image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: Extracted text from the image.

    Raises:
        NoTextFoundError: If no text is found in the image.
    """
    image = Image.open(image_path)
    image = preprocess_image(image)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)
    
    if not text.strip():
        raise NoTextFoundError(f"No text found in {image_path}")
    
    return text

def extract_text_from_directory(directory_path):
    """
    Iterates through every image file in a directory to extract any text and numbers.

    Args:
        directory_path (str): The path to the directory containing image files.

    Returns:
        dict: A dictionary with image file names as keys and extracted text as values.
    """
    text_dict = {}
    supported_extensions = ('.jpg', '.jpeg', '.png', '.tiff', '.dng', '.bmp', '.gif')

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(supported_extensions):
            file_path = os.path.join(directory_path, filename)
            try:
                extracted_text = extract_text_and_numbers(file_path)
                text_dict[filename] = extracted_text
            except NoTextFoundError as e:
                print(e)
    
    return text_dict

if __name__ == "__main__":
    # Example usage
    directory_path = 'images'  # Directory containing images
    text_dict = extract_text_from_directory(directory_path)
    for filename, text in text_dict.items():
        print(f"{filename}: {text}")
