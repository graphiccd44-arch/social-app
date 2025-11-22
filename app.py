import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(data):
    # Extract Data
    topic = data.get('topic')
    platform = data.get('platform', 'Facebook')
    tone = data.get('tone', 'Professional')
    age = data.get('age', 'Any')
    gender = data.get('gender', 'All')
    persona = data.get('persona', '')
    length = data.get('length', 'Medium')
    category = data.get('category', 'Awareness')
    language = data.get('language', 'Myanglish')
    ai_model = data.get('ai_model', 'Gemini 2.5 Flash')
    
    # Refinement Mode (Magic Buttons)
    refine_instruction = data.get('refine_instruction')
    current_text = data.get('current_text')

    # Model Selection
    target_model_id = 'gemini-2.0-flash' 
    if ai_model == "Gemini 3.0 Pro": target_model_id = 'gemini-3-pro-preview'
    elif ai_model == "Gemini 2.5 Flash": target_model_id = 'gemini-2.5-flash'
    elif ai_model in ["DeepSeek", "ChatGPT"]: target_model_id = 'gemini-2.5-flash'

    try:
        model = genai.GenerativeModel(target_model_id, generation_config={"response_mime_type": "application/json"})
    except:
        model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})

    # Logic Switch: Refinement vs New Generation
    if refine_instruction and current_text:
        # --- REFINEMENT PROMPT ---
        prompt = f"""
        Act as a Professional Editor.
        Original Text: "{current_text}"
        
        Task: Rewrite the text above based on this instruction: "{refine_instruction}"
        
        Constraints:
        - Keep the same language style ({language}).
        - Keep formatting suitable for {platform}.
        
        Output strictly in JSON format with a single key: "post_content".
        """
    else:
        # --- NEW GENERATION PROMPT ---
        audience_profile = f"{gender}, aged {age}"
        if persona: audience_profile += f", specifically {persona}"

        length_instr = "100-150 words"
        if length == "Short": length_instr = "under 50 words"
        elif length == "Long": length_instr = "over 200 words"

        lang_instr = "Burmese (Myanmar) mixed with English keywords naturally (Myanglish)."
        if language == "Pure Burmese": lang_instr = "STRICTLY BURMESE ONLY."
        elif language == "English Only": lang_instr = "STRICTLY ENGLISH ONLY."

        model_persona = "You are an expert Social Media Manager."
        if ai_model == "DeepSeek": model_persona = "Act as DeepSeek. Logical, factual."
        elif ai_model == "ChatGPT": model_persona = "Act as ChatGPT. Conversational, creative."

        prompt = f"""
        {model_persona}
        Platform: {platform}
        Topic: {topic}
        Audience: {audience_profile}
        Goal: {category}
        Tone: {tone}
        Length: {length_instr}
        LANGUAGE: {lang_instr}

        FORMATTING:
        - Use Line breaks for readability.
        - Use Bold (**) for emphasis.
        - Use Emojis.

        Output strictly in JSON format with a single key: "post_content".
        """
    
    try:
        response = model.generate_content(prompt)
        if not response.text: return {"post_content": "Error: Empty response."}
        
        try:
            data = json.loads(response.text)
            if isinstance(data, list): data = data[0] if len(data) > 0 else {}
        except:
            return {"post_content": response.text}

        content = data.get("post_content") or str(data)
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
    result = generate_content(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
