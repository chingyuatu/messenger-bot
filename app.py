import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from google import genai

app = Flask(__name__)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

chat_history = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.values.get("Body", "").strip()
    sender = request.values.get("From", "")

    print("Received message: " + incoming_msg)

    if sender not in chat_history:
        chat_history[sender] = []

    chat_history[sender].append({
        "role": "user",
        "parts": [{"text": incoming_msg}]
    })

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=chat_history[sender]
        )
        reply_text = response.text
        print("Gemini reply: " + reply_text)

        chat_history[sender].append({
            "role": "model",
            "parts": [{"text": reply_text}]
        })

        if len(chat_history[sender]) > 20:
            chat_history[sender] = chat_history[sender][-20:]

    except Exception as e:
        reply_text = "Error: " + str(e)
        print("Error: " + str(e))

    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

@app.route("/", methods=["GET"])
def index():
    return "WhatsApp Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
