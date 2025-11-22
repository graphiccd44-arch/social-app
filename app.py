import os
import json
import traceback
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(data):
    try:
        # Data Extraction
        topic = data.get('topic', '')
        platform = data.get('platform', 'Facebook')
        tone = data.get('tone', 'Professional')
        length = data.get('length', 'Medium') # Length is back!
        category = data.get('category', 'Awareness')
        language = data.get('language', 'Myanglish')
        ai_model = data.get('ai_model', 'Gemini 2.5 Flash')
        creativity = data.get('creativity', 'Standard') # New Feature
        
        # Refinement
        refine_instruction = data.get('refine_instruction')
        current_text = data.get('current_text')

        # Model Selection
        target_model_id = 'gemini-2.0-flash' 
        if ai_model == "Gemini 3.0 Pro": target_model_id = 'gemini-3-pro-preview'
        elif ai_model == "Gemini 2.5 Flash": target_model_id = 'gemini-2.5-flash'
        elif ai_model in ["DeepSeek", "ChatGPT"]: target_model_id = 'gemini-2.5-flash'

        # Configure high temperature for creativity
        gen_config = {
            "response_mime_type": "application/json",
            "temperature": 0.9 if creativity != "Standard" else 0.7 # Higher temp = More Creative
        }

        try:
            model = genai.GenerativeModel(target_model_id, generation_config=gen_config)
        except:
            model = genai.GenerativeModel('gemini-2.0-flash', generation_config=gen_config)

        # Prompt Building
        prompt = ""
        
        if refine_instruction and current_text:
            # Refinement Logic
            prompt = f"""
            Act as a Creative Editor.
            Original: "{current_text}"
            Task: Rewrite based on: "{refine_instruction}"
            Constraints: Keep language ({language}).
            Output JSON with key: "post_content".
            """
        else:
            # --- New Content Logic ---
            
            # Length Strictness
            length_instr = "around 100-150 words"
            if length == "Short": length_instr = "Very short, punchy, under 60 words (Strictly)."
            elif length == "Long": length_instr = "Long-form, storytelling style, over 250 words (Strictly)."

            # Creativity Logic
            creative_instr = "Standard social media post."
            if creativity == "Storytelling":
                creative_instr = "Start with a hook/story. Use emotional triggers. Do NOT sound robotic. Use metaphors."
            elif creativity == "Viral/Hook":
                creative_instr = "Start with a controversial or shocking statement. High energy. Short sentences. Designed to go viral."
            elif creativity == "Direct/Sales":
                creative_instr = "Focus on pain points and solutions. Use psychological triggers (FOMO). Strong CTA."

            lang_instr = "Burmese (Myanmar) mixed with English keywords naturally (Myanglish)."
            if language == "Pure Burmese": lang_instr = "STRICTLY BURMESE ONLY."
            elif language == "English Only": lang_instr = "STRICTLY ENGLISH ONLY."

            model_persona = "You are a top-tier Creative Copywriter."
            if ai_model == "DeepSeek": model_persona = "Act as DeepSeek. Logical, factual, detailed."
            elif ai_model == "ChatGPT": model_persona = "Act as ChatGPT. Conversational, human-like."

            prompt = f"""
            {model_persona}
            Platform: {platform}
            Topic: {topic}
            Goal: {category}
            Tone: {tone}
            
            CRITICAL INSTRUCTIONS:
            1. Length: {length_instr}
            2. Creativity Style: {creative_instr}
            3. Language: {lang_instr}
            4. Formatting: Use bolding for emphasis. Use proper line breaks.

            Output strictly in JSON format with a single key: "post_content".
            """
        
        response = model.generate_content(prompt)
        
        if not response.text: return {"post_content": "Error: No response from AI."}

        try:
            parsed = json.loads(response.text)
            if isinstance(parsed, list): parsed = parsed[0] if parsed else {}
        except:
            return {"post_content": response.text}

        final_content = parsed.get("post_content") or str(parsed)
        return {"post_content": final_content}

    except Exception as e:
        print(f"Gen Error: {e}")
        return {"post_content": f"Error: {str(e)}"}

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
    try:
        if not session.get('logged_in'): return jsonify({'result': 'Unauthorized'}), 401
        data = request.json
        result = generate_content(data)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"post_content": f"Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
