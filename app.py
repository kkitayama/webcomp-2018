import requests
import json
import base64
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug import secure_filename

from os.path import join, dirname
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

API_KEY = os.environ.get("API_KEY")


def text_detection(image_path):
    api_url = 'https://vision.googleapis.com/v1/images:annotate?key={}'.format(API_KEY)
    with open(image_path, "rb") as img:
        image_content = base64.b64encode(img.read())
        req_body = json.dumps({
            'requests': [{
                'image': {
                    'content': image_content.decode('utf-8')  # base64でエンコードしたものjsonにするためdecodeする
                },
                'features': [{
                    'type': 'TEXT_DETECTION'
                }]
            }]
        })
        res = requests.post(api_url, data=req_body)
        return res.json()

def extract_text(image_path):
    res_json = text_detection(image_path)
    res_text = res_json["responses"][0]["textAnnotations"][0]["description"]
    return res_text

def tarnslate_per_line(text, language):
    result_list = []
    sent_in = text
    sent_list = sent_in.split('\n')
    for sent in sent_list:
        url="https://translation.googleapis.com/language/translate/v2"
        url += "?key=" + API_KEY
        url += "&q=" + sent
        # url += "&source=en&target=ja"
        url += "&target=" + language

        rr=requests.get(url)
        unit_aa=json.loads(rr.text)
        result_list.append(unit_aa["data"]["translations"][0]["translatedText"])
    result = '\n'.join(result_list)
    return result

def tarnslate_all(text, language):
    result_list = []
    sent = text
    url="https://translation.googleapis.com/language/translate/v2"
    url += "?key=" + API_KEY
    url += "&q=" + sent
    # url += "&source=en&target=ja"
    url += "&target=" + language

    rr=requests.get(url)
    unit_aa=json.loads(rr.text)
    result_list.append(unit_aa["data"]["translations"][0]["translatedText"])
    result = '\n'.join(result_list)
    return result

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['SECRET_KEY'] = os.urandom(24)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send', methods=['GET', 'POST'])
def send():
    if request.method == 'POST':
        try:
            img_file = request.files['img_file']
        except:
            img_file = None
        if img_file and allowed_file(img_file.filename):
            filename = secure_filename(img_file.filename)
            img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_url = '/uploads/' + filename
            try:
                source_text = extract_text('.' + img_url)
                # print(source_text)
                return render_template('index.html', img_url=img_url, source_text=source_text)
            except:
                error_message = "Sorry, we could not find any letters in the image."
                return render_template('index.html', img_url=img_url, error_message=error_message)
            return render_template('index.html', img_url=img_url, source_text=source_text)
        else:
            error_message = "No input or the data type is not supported."
            return render_template('index.html', error_message=error_message)
    else:
        return redirect(url_for('index'))

@app.route('/send/translate', methods=['POST'])
def translate():
    modified_text = request.form['query']
    language = request.form['language']
    option = request.form['action']
    # print(language)
    img_url = request.form['img_url']
    # print(modified_text)
    if (language == 'no_lang'):
        translated_text = modified_text
    else:
        if option == 'Translate all':
            translated_text = tarnslate_all(modified_text, language)
        elif option == 'Translate per line':
            translated_text = tarnslate_per_line(modified_text, language)
    # print(translated_text)
    return render_template('index.html', img_url=img_url, source_text=modified_text, translated_text=translated_text)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.debug = True
    app.run()
