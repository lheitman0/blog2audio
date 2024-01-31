from flask import Flask, request, render_template, send_file
import os
import requests
from bs4 import BeautifulSoup
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
    
    response = requests.get(url)
    web_content = response.text
    
    soup = BeautifulSoup(web_content, 'html.parser')
    text = soup.get_text(separator='\n')
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input= text,
    )

    audio_path = "static/audio_output.mp3"
    with open(audio_path, "wb") as audio_file:
        audio_file.write(response.content)
    
    
    return render_template('result.html', text=text, audio_path=audio_path)

if __name__ == '__main__':
    app.run(debug=True)
