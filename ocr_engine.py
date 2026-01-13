import cv2
import pytesseract
import numpy as np
import pandas as pd

# Step 1: Image Load karna
def load_image(image_path):
    print(f"Loading image from: {image_path}")
    return cv2.imread(image_path)

# Step 2: Text nikalna (OCR)
def extract_text(image):
    # Image ko Black & White karna (Preprocessing)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Text nikalna
    text = pytesseract.image_to_string(gray)
    return text

# Main Function
if __name__ == "__main__":
    print("--- AI Identity Verification System Started ---")
    print("Waiting for Aadhaar/PAN Card image...")
    # Yahan future mein image path aayega