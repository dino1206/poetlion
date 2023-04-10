import cv2
import pytesseract
import numpy as np
import os
import re
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,ImageMessage
import requests
from linebot import LineBotApi, WebhookHandler



line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default = "true").lower() == "true"

def read_image_from_url(url):
    image_data = requests.get(url).content
    return np.asarray(bytearray(image_data), dtype=np.uint8)

def recognize_text_in_image(image_url):
    image_data = read_image_from_url(image_url)
    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    adaptive_threshold = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,11,2)
    text = pytesseract.image_to_string(adaptive_threshold, lang='chi_tra')
    return text

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
    image_data = np.asarray(bytearray(image_content.content), dtype=np.uint8)
    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    adaptive_threshold = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv2.THRESH_BINARY,11,2)
    text = pytesseract.image_to_string(adaptive_threshold, lang='chi_tra')
    text = re.sub(r'\s+', '', text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text)
    )


if __name__ == "main":
    app.run()
