import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, age, gender, persona, length, category, language, art_style, ai_model):
    
    # --- MODEL SELECTION LOGIC (NEW) ---
    # UI က ရွေးလိုက်တဲ့ နာမည်အလိုက် Model အစစ်ကို ချိတ်ပေးခြင်း
    target_model_id = 'gemini-2.0-flash' # Default

    if ai_model == "Gemini 3.0 Pro":
        target_model_id = 'gemini-3-pro-preview' # The Big Boss
    elif ai_model == "Gemini 2.5 Flash":
        target_model_id = 'gemini-2.5-flash'     # Faster & Smarter
    elif ai_model == "Gemini 2.5 Pro":
        target_model_id = 'gemini-2.5-pro'       # High Quality
    
    # DeepSeek နဲ့ ChatGPT Style အတွက်ကတော့ 2.5 Flash ကိုပဲ Engine အဖြစ်သုံးပြီး Persona ပြောင်းမယ်
    elif ai_model in ["DeepSeek", "ChatGPT"]:
        target_model_id = 'gemini-2.5-flash'

    model = genai.GenerativeModel(target_model_id, generation_config={"response_mime_type": "application/json"})
    
    # Audience
    audience_profile = f"{gender}, aged {age}"
    if persona: audience_profile += f", specifically {persona}"

    # Length
    length_instruction = "standard length (100-150 words)"
    if length == "Short": length_instruction = "very short, punchy (under 50 words)"
    elif length == "Long": length_instruction = "long-form, detailed (over 200 words)"

    # Language
    lang_instruction = "Burmese (Myanmar) mixed with English keywords naturally (Myanglish)."
    if language == "Pure Burmese": lang_instruction = "STRICTLY BURMESE (Myanmar) ONLY. No English words."
    elif language == "English Only": lang_instruction = "STRICTLY ENGLISH ONLY."

    # Persona Logic
    model_persona = "You are an expert AI Social Media Manager."
    if ai_model == "DeepSeek":
        model_persona = "Act as DeepSeek-V3. Be extremely logical, analytical, and data-driven. Focus on facts."
    elif ai_model == "ChatGPT":
        model_persona = "Act as ChatGPT-4o. Be conversational, friendly, creative, and human-like."
    elif ai_model == "Gemini 3.0 Pro":
        model_persona = "You are Gemini 3.0. Show off your advanced reasoning and creativity."

    prompt = f"""
    {model_persona}
    Role: Senior Social Media Manager.
    Platform: {platform}
    
    REQUIREMENTS:
    - Topic: {topic}
    - Target Audience: {audience_profile}
    - Goal: {category}
    - Tone: {tone}
    - Length: {length_instruction}
    - LANGUAGE: {lang_instruction} (Critical)

    Image Style: {art_style}

    Output strictly in JSON format with keys: "post_content" and "image_prompt".
    Do not wrap in a list.
    """
    
    try:
        response = model.generate_content(prompt)
        if not response.text: return {"post_content": "Error: Empty response.", "image_prompt": ""}
        
        try:
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0] if len(data) > 0 else {}
        except:
            return {"post_content": response.text, "image_prompt": f"{art_style} image of {topic}"}

        content = data.get("post_content") or data.get("caption") or str(data)
        img_prompt = data.get("image_prompt") or f"{art_style} image of {topic}"
        
        return {"post_content": content, "image_prompt": img_prompt + ", high quality, 8k"}

    except Exception as e:
        return {"post_content": f"System Error ({target_model_id}): {str(e)}", "image_prompt": ""}

# Model List ကို စစ်ဖို့ Endpoint (Optional)
@app.route('/models')
def check_models():
    try:
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return jsonify({"Available Models": model_list})
    except Exception as e: return f"Error: {str(e)}"

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
        data.get('topic', ''), data.get('platform', 'Facebook'), data.get('tone', 'Professional'),
        data.get('age', 'Any Age'), data.get('gender', 'All'), data.get('persona', ''),
        data.get('length', 'Medium'), data.get('category', 'Brand Awareness'),
        data.get('language', 'Myanglish'), data.get('art_style', 'Realistic'),
        data.get('ai_model', 'Gemini 2.5 Flash')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
