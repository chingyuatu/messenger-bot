import os
import logging
from flask import Flask, request
from google import genai
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

chat_history = {}

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified!")
        return challenge, 200
    else:
        return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    logger.info("Received: " + str(data))

    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                if "message" in event:
                    sender_id = event["sender"]["id"]
                    incoming_msg = event["message"].get("text", "")

                    if not incoming_msg:
                        continue

                    if sender_id not in chat_history:
                        chat_history[sender_id] = []

                    chat_history[sender_id].append({
                        "role": "user",
                        "parts": [{"text": incoming_msg}]
                    })

                    try:
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=chat_history[sender_id]
                        )
                        reply_text = response.text

                        chat_history[sender_id].append({
                            "role": "model",
                            "parts": [{"text": reply_text}]
                        })

                        if len(chat_history[sender_id]) > 20:
                            chat_history[sender_id] = chat_history[sender_id][-20:]

                    except Exception as e:
                        reply_text = "Error: " + str(e)
                        logger.error("Error: " + str(e))

                    send_message(sender_id, reply_text)

    return "OK", 200

def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v18.0/me/messages?access_token=" + PAGE_ACCESS_TOKEN
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    response = requests.post(url, json=payload)
    logger.info("Sent: " + str(response.json()))

@app.route("/", methods=["GET"])
def index():
    return "Messenger Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
