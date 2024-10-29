import cv2
from PIL import Image
import pytesseract

# Load the image
image = cv2.imread("screenshots/screenshot.png")

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply thresholding
_, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

# Save and use pytesseract
preprocessed_image = Image.fromarray(binary_image)
text = pytesseract.image_to_string(preprocessed_image)
print(text)
