import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "change-this-later")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v23.0")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Bot + AI is online! 🤖", 200


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]

        if message.get("type") == "text":
            text = message["text"]["body"].strip()

            if text.lower() == "/ping":
                reply = "Pong! 🏓"

            elif text.lower() == "/menu":
                reply = (
                    "🤖 *Bot Menu*\n\n"
                    "/menu - Show menu\n"
                    "/ping - Test bot\n"
                    "/help - Get help\n"
                    "/ai <message> - Ask AI"
                )

            elif text.lower() == "/help":
                reply = "Use /menu to see my commands. 😎"

            elif text.lower().startswith("/ai "):
                question = text[4:].strip()

                response = client.responses.create(
                    model="gpt-5.6-luna",
                    input=question
                )

                reply = response.output_text

            else:
                reply = f"You said: {text}"

            send_message(sender, reply)

    except Exception as error:
        print("Error:", error)

    return "OK", 200


def send_message(to, message):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("WhatsApp credentials are not configured yet.")
        return

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=20
    )

    print("WhatsApp API:", response.status_code, response.text)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
