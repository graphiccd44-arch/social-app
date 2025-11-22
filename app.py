import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, age, gender, persona, length, category, language, ai_model):
    
    # Model Selection
    target_model_id = 'gemini-2.0-flash' 
    if ai_model == "Gemini 3.0 Pro": target_model_id = 'gemini-3-pro-preview'
    elif ai_model == "Gemini 2.5 Flash": target_model_id = 'gemini-2.5-flash'
    elif ai_model == "Gemini 2.5 Pro": target_model_id = 'gemini-2.5-pro'
    elif ai_model in ["DeepSeek", "ChatGPT"]: target_model_id = 'gemini-2.5-flash'

    try:
        model = genai.GenerativeModel(target_model_id, generation_config={"response_mime_type": "application/json"})
    except:
        # Fallback if model not found
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})

    # Setup Logic
    audience_profile = f"{gender}, aged {age}"
    if persona: audience_profile += f", specifically {persona}"

    length_instruction = "standard length (100-150 words)"
    if length == "Short": length_instruction = "very short, punchy (under 50 words)"
    elif length == "Long": length_instruction = "long-form, detailed (over 200 words)"

    lang_instruction = "Burmese (Myanmar) mixed with English keywords naturally (Myanglish)."
    if language == "Pure Burmese": lang_instruction = "STRICTLY BURMESE (Myanmar) ONLY."
    elif language == "English Only": lang_instruction = "STRICTLY ENGLISH ONLY."

    model_persona = "You are an expert AI Social Media Manager."
    if ai_model == "DeepSeek": model_persona = "Act as DeepSeek-V3. Logical, concise, factual."
    elif ai_model == "ChatGPT": model_persona = "Act as ChatGPT-4o. Conversational, creative."

    prompt = f"""
    {model_persona}
    Platform: {platform}
    Topic: {topic}
    Target Audience: {audience_profile}
    Goal: {category}
    Tone: {tone}
    Length: {length_instruction}
    LANGUAGE: {lang_instruction}

    Output strictly in JSON format with a single key: "post_content".
    Do NOT include image prompts.
    """
    
    try:
        response = model.generate_content(prompt)
        if not response.text: return {"post_content": "Error: Empty response."}
        
        try:
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0] if len(data) > 0 else {}
        except:
            # JSON မဟုတ်ရင် စာသားအတိုင်းယူမယ်
            return {"post_content": response.text}

        content = data.get("post_content") or data.get("caption") or str(data)
        return {"post_content": content}

    except Exception as e:
        return {"post_content": f"System Error: {str(e)}"}

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
    # art_style ဖြုတ်လိုက်ပါပြီ
    result = generate_content(
        data.get('topic', ''), data.get('platform', 'Facebook'), data.get('tone', 'Professional'),
        data.get('age', 'Any Age'), data.get('gender', 'All'), data.get('persona', ''),
        data.get('length', 'Medium'), data.get('category', 'Brand Awareness'),
        data.get('language', 'Myanglish'), data.get('ai_model', 'Gemini 2.5 Flash')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
