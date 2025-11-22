import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, age, gender, persona, length, category):
    # JSON Mode ကို သုံးထားပေမယ့် တခါတလေ AI က လွဲတတ်လို့ Error handling ကောင်းကောင်းလုပ်ရမယ်
    model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
    
    audience_profile = f"{gender}, aged {age}"
    if persona: audience_profile += f", specifically {persona}"

    length_instruction = "standard length (100-150 words)"
    if length == "Short": length_instruction = "very short (under 50 words)"
    elif length == "Long": length_instruction = "long-form (over 200 words)"

    category_instruction = "General social media post"
    if category == "Brand Awareness": category_instruction = "Focus on storytelling, brand identity."
    elif category == "Engagement": category_instruction = "Focus on interaction, questions, polls."
    elif category == "Educational": category_instruction = "Focus on teaching, tips, how-to guides."
    elif category == "Copywriting": category_instruction = "Focus on sales, persuasion, strong CTA."

    prompt = f"""
    Act as a Social Media Manager.
    Create a post for {platform}.
    
    Details:
    - Topic: {topic}
    - Audience: {audience_profile}
    - Goal: {category} ({category_instruction})
    - Tone: {tone}
    - Length: {length_instruction}

    Output strictly in JSON format with keys: "post_content" and "image_prompt".
    """
    
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            return {"post_content": "Error: AI returned empty response (Safety Block). Try a different topic.", "image_prompt": ""}

        # JSON Parsing
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            # JSON မဟုတ်ဘဲ စာသားအတိုင်း ထွက်လာခဲ့ရင်
            return {"post_content": response.text, "image_prompt": "A generic social media image"}

        # Safe Get (Key မရှိရင် Error မတက်အောင် ကာကွယ်ခြင်း)
        content = data.get("post_content") or data.get("caption") or data.get("content") or str(data)
        img_prompt = data.get("image_prompt") or data.get("image_description") or "Social media background"

        return {"post_content": content, "image_prompt": img_prompt}

    except Exception as e:
        return {"post_content": f"System Error: {str(e)}", "image_prompt": ""}

@app.route('/', methods=['GET', 'POST'])
def home():
    if not session.get('logged_in'):
        error = None
        if request.method == 'POST':
            if request.form.get('password') == APP_PASSWORD:
                session['logged_in'] = True
                return redirect(url_for('home'))
            else:
                error = "စကားဝှက် မှားယွင်းနေပါတယ်!"
        return render_template('index.html', show_login=True, error=error)
    return render_template('index.html', show_login=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/generate', methods=['POST'])
def generate():
    if not session.get('logged_in'): return jsonify({'result': 'Unauthorized'}), 401
    data = request.json
    result = generate_content(
        data.get('topic'), data.get('platform'), data.get('tone'),
        data.get('age'), data.get('gender'), data.get('persona'),
        data.get('length'), data.get('category') 
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
