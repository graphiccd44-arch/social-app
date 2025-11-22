import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, age, gender, persona, length, category, language, art_style):
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

    # --- LANGUAGE FIX START ---
    # မြန်မာလိုရေးဖို့ အမိန့်ကို ပိုတင်းကျပ်လိုက်ပါတယ်
    lang_instruction = "MAIN LANGUAGE MUST BE BURMESE (Myanmar) mixed with English keywords naturally."
    
    if language == "Pure Burmese": 
        lang_instruction = "MAIN LANGUAGE MUST BE STRICTLY BURMESE (Myanmar) ONLY. Do not use English words."
    elif language == "English Only": 
        lang_instruction = "Write in English language only."
    elif language == "Myanglish":
        lang_instruction = "Write primarily in Burmese (Myanmar script) but mix in English slang/keywords naturally."
    # --- LANGUAGE FIX END ---

    prompt = f"""
    Act as a Senior Social Media Manager for a Myanmar audience.
    Create a post for {platform}.
    
    STRICT LANGUAGE REQUIREMENT: {lang_instruction}
    
    Details:
    - Topic: {topic}
    - Audience: {audience_profile}
    - Goal: {category} ({category_instruction})
    - Tone: {tone}
    - Length: {length_instruction}

    Image Requirement:
    - Style: {art_style} (Create a prompt that generates an image in this specific art style)

    Output strictly in JSON format with keys: "post_content" and "image_prompt".
    Do not wrap the JSON in a list. Return a single object.
    """
    
    try:
        response = model.generate_content(prompt)
        
        if not response.text:
            return {"post_content": "Error: AI returned empty response.", "image_prompt": ""}

        try:
            data = json.loads(response.text)
            if isinstance(data, list):
                if len(data) > 0: data = data[0]
                else: data = {}
        except json.JSONDecodeError:
            return {"post_content": response.text, "image_prompt": f"{art_style} image of {topic}"}

        content = data.get("post_content") or data.get("caption") or str(data)
        img_prompt = data.get("image_prompt") or f"{art_style} image of {topic}"
        img_prompt = f"{img_prompt}, {art_style} style, high quality, 8k"

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
        data.get('topic', ''), 
        data.get('platform', 'Facebook'), 
        data.get('tone', 'Professional'),
        data.get('age', 'Any Age'), 
        data.get('gender', 'All'), 
        data.get('persona', ''),
        data.get('length', 'Medium'), 
        data.get('category', 'Brand Awareness'),
        data.get('language', 'Myanglish'),
        data.get('art_style', 'Realistic')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
