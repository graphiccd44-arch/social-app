import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

# Session အတွက် Secret Key (Render မှာ ပြောင်းလို့ရပါတယ်)
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")

# စကားဝှက် (Render မှာ APP_PASSWORD ဆိုပြီး ပြောင်းလို့ရပါတယ်)
# Default ကတော့ '12345' ပါ
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")

# API Key Setup
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, audience, length):
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Length ကို Prompt မှာ ထည့်သွင်းခြင်း
    length_instruction = ""
    if length == "Short":
        length_instruction = "Keep it very short, punchy, and concise (under 50 words)."
    elif length == "Long":
        length_instruction = "Write a detailed, long-form post with storytelling (over 200 words)."
    else:
        length_instruction = "Keep it standard length (around 100-150 words)."

    prompt = f"""
    Act as a professional Social Media Manager for Myanmar audience.
    Create a post for {platform}.
    
    Details:
    - Topic: {topic}
    - Target Audience: {audience}
    - Tone: {tone}
    - Length Instruction: {length_instruction}
    
    Instructions:
    1. Start with a Hook.
    2. Use natural Burmese mixed with English (Burmese-English style).
    3. Use emojis and hashtags.
    4. Include a Call to Action (CTA).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def home():
    # Login ဝင်မထားရင် Login စာမျက်နှာပြမယ်
    if not session.get('logged_in'):
        error = None
        if request.method == 'POST':
            if request.form.get('password') == APP_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('home'))
            else:
                error = "စကားဝှက် မှားယွင်းနေပါတယ်!"
        return render_template('index.html', show_login=True, error=error)

    # Login ဝင်ပြီးရင် App ကို ပြမယ်
    return render_template('index.html', show_login=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
def generate():
    if not session.get('logged_in'):
        return jsonify({'result': 'Unauthorized'}), 401

    data = request.json
    return jsonify({'result': generate_content(
        data.get('topic'), 
        data.get('platform'), 
        data.get('tone'), 
        data.get('audience'),
        data.get('length') # အသစ်ပါလာတဲ့ Length
    )})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
