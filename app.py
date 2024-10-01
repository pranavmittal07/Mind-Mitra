from flask import Flask, render_template, request, jsonify, session
import requests
from datetime import timedelta
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session expiry time

GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'
API_KEY = app.config["GEMINI_API_KEY"]

# Initialize conversation history in the session
def init_conversation_history():
    if 'conversation_history' not in session:
        session['conversation_history'] = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    # Initialize conversation history if it's the first message
    init_conversation_history()

    # Add an initial system message to guide the conversation
    if len(session['conversation_history']) == 0:
        # This instruction acts as a guideline for the chatbot
        initial_instruction = "You are a mental health and emotional support assistant. Provide guidance, support, and compassionate advice in all responses."
        session['conversation_history'].append({"text": initial_instruction})

    # Append the user's message to the conversation history
    session['conversation_history'].append({"text": user_message})

    # Prepare the payload with the conversation history
    data = {
        "contents": [
            {
                "parts": session['conversation_history']
            }
        ]
    }

    response = requests.post(
        f'{GEMINI_API_URL}?key={API_KEY}',
        headers={'Content-Type': 'application/json'},
        json=data
    )
    
    if response.status_code == 200:
        response_data = response.json()
        try:
            # Check for safety reason
            if response_data['candidates'][0].get('finishReason') == 'SAFETY':
                reply = "Sorry, the conversation contains inappropriate language. Let's keep it respectful."
            else:
                # Extract the bot's reply text
                bot_reply = response_data['candidates'][0]['content']['parts'][0]['text']
                
                # Append the bot's reply to the conversation history
                session['conversation_history'].append({"text": bot_reply})
                reply = bot_reply
        except (KeyError, IndexError) as e:
            reply = f"Error: Missing key in response ({str(e)}), full response: {response_data}"
    else:
        reply = f"Error: {response.status_code}, {response.text}"

    return jsonify({'reply': reply})

# Clear conversation history endpoint (optional)
@app.route('/clear', methods=['POST'])
def clear_history():
    session.pop('conversation_history', None)
    return jsonify({'message': 'Conversation history cleared.'})

if __name__ == '__main__':
    app.run(debug=True)
