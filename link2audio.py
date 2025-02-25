from flask import Flask, request, render_template, send_file
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()
OpenAI.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_url():
    url = request.form['url']

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(url)

    # Wait for the page to load and execute JavaScript
    driver.implicitly_wait(10)

    # Extract the text content
    web_content = driver.page_source
    text = driver.find_element_by_tag_name('body').text

    # Close the browser
    driver.quit()

    response_audio = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )

    audio_path = "static/audio_output.mp3"
    with open(audio_path, "wb") as audio_file:
        audio_file.write(response_audio.content)

    return render_template('result.html', text=text, audio_path=audio_path)

if __name__ == '__main__':
    app.run(debug=True)