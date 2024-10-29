from flask import Flask, render_template, request, send_file, send_from_directory, jsonify
import requests
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import base64
import os
from io import BytesIO
import pytesseract
from PIL import Image
import cv2

app = Flask(__name__)

Characters_per_minute = 1200

chrome_options = Options()
chrome_options = Options()
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")  # Linux only
chrome_options.add_argument("--headless=old")     # Enable headless mode
chrome_options.add_argument("window-size=1920x1080")  # Set window size
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")

CACHE_FILE = 'cache.json'  # Single JSON file for caching



@app.route('/', methods=['GET', 'POST'])
def index():
    html_content = ''
    md_images = []

    if request.method == 'POST':
        url = request.form['url']

        # Load existing cache
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
        else:
            cache_data = {}

        # Check if the URL is already cached
        if url in cache_data:
            md_images = cache_data[url]['md_images']
            next_chapter = cache_data[url].get('next_chapter')
            prev_chapter = cache_data[url].get('prev_chapter')
            html_content = f"Next: {next_chapter}, Previous: {prev_chapter}"
        else:
            # Create a new driver instance for each request
            driver = webdriver.Chrome(options=chrome_options)

            driver.get(url)

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "__NEXT_DATA__"))
                )

                script_tag = driver.find_element(By.ID, "__NEXT_DATA__")
                script_content = script_tag.get_attribute("innerHTML")

                # Parse the JSON to extract md_images
                data = json.loads(script_content)

                # Navigate through the JSON structure to find md_images
                md_images = data['props']['pageProps']['chapter'].get('md_images', [])
                next_chapter = data['props']['pageProps'].get('next')
                prev_chapter = data['props']['pageProps'].get('prev')
                html_content = f"Next: {next_chapter}, Previous: {prev_chapter}"

                # Update cache data
                cache_data[url] = {
                    'md_images': md_images,
                    'next_chapter': next_chapter,
                    'prev_chapter': prev_chapter
                }

                # Save updated cache
                with open(CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f, indent=4)

            except Exception as e:
                html_content = str(e)

            finally:
                driver.quit()  # Ensure the driver is closed
    print(md_images)
    return render_template('index.html', html_content=html_content, md_images=md_images)


@app.route('/save-screenshot', methods=['POST'])
def save_screenshot():
    if 'image' not in request.files:
        return 'No image part', 400

    file = request.files['image']
    
    # Save the image to a directory
    save_path = os.path.join('screenshots', file.filename)  # Specify the save directory
    file.save(save_path)

    # Use OCR to extract text from the image
    print(save_path)
    text = extract_text_from_image(save_path)
    
    # Calculate time based on number of words (example: 200 words per minute)
    char_count = len(text)
    # Assuming an average reading speed of 1200 characters per minute
    time_per_character = 60 / 1500  # Time in seconds per character
    total_time = int(char_count * time_per_character * 1000)  # Convert to milliseconds
    print(total_time)
    if total_time == 0: total_time = 300
    return jsonify({'time': total_time}), 200


def extract_text_from_image(image_path):
    """Extract text from an image using Tesseract OCR."""
    # Open the image using PIL
    # img = Image.open(image_path)
    # Use pytesseract to extract text
    # text = pytesseract.image_to_string(img)
    image = cv2.imread(image_path)

# Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding
    _, binary_image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Save and use pytesseract
    preprocessed_image = Image.fromarray(binary_image)
    text = pytesseract.image_to_string(preprocessed_image)
    return text

@app.route('/test-save-screenshot', methods=['POST'])
def test_save_screenshot():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']
    
    # Save the image to a temporary directory
    save_path = os.path.join('screenshots', f'test_{file.filename}')  # Specify the save directory
    file.save(save_path)

    # Optional: Log the save path to verify
    print(f'Screenshot saved at: {save_path}')
    
    return jsonify({'message': 'Screenshot saved successfully!'}), 200


def update_reading_speed(new_speed):
    with open('data.json', 'r+') as file:
        data = json.load(file)
        data['characters_per_minute'] = new_speed
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


@app.route('/update_speed', methods=['POST'])
def update_speed():
    data = request.get_json()
    new_speed = data.get('characters_per_minute')
    update_reading_speed(new_speed)
    return jsonify({'message': 'Reading speed updated'}), 200

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('manhwa_images', filename)


if __name__ == '__main__':
    app.run(debug=True)
