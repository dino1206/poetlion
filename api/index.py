from io import BytesIO
import requests
import os
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,ImageMessage

import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

def read_image_from_url(url):
    image_data = requests.get(url).content
    return BytesIO(image_data)

def recognize_text_in_image(image_url):
    image_file = read_image_from_url(image_url)
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'image': image_file},
        data={'apikey': 'K83057456588957',
              'language': 'chi_tra'}
    )
    response_data = response.json()
    if response_data['OCRExitCode'] != 1:
        return None
    return response_data['ParsedResults'][0]['ParsedText']


app = Flask(__name__)

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global working_status

    if event.message.type != "text":
        return

    if event.message.text == "啟動":
        working_status = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我是時下流行的AI智能，目前可以為您服務囉，歡迎來跟我互動~"))
        return

    if event.message.text == "安靜":
        working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="感謝您的使用，若需要我的服務，請跟我說 「啟動」 謝謝~"))
        return
	
@line_handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    global working_status
    if not working_status:
        return
    image_id = event.message.id
    image_content = line_bot_api.get_message_content(image_id)
    image_file = BytesIO(image_content.content)
    response = requests.post(
        'https://api.ocr.space/parse/image',
        files={'image': image_file},
        data={'apikey': 'K83057456588957',
              'language': 'chi_tra'}
    )
    response_data = response.json()
    if response_data['OCRExitCode'] != 1:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，無法識別圖片中的文字，請再試一次~")
        )
        return
    text = response_data['ParsedResults'][0]['ParsedText']
    text = re.sub(r'\s+', '', text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )


if __name__ == "main":
    app.run()
