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

# --- LOGIC ---
def generate_content(data):
    try:
        # Data Extraction
        topic = data.get('topic', '')
        platform = data.get('platform', 'Facebook')
        tone = data.get('tone', 'Professional')
        age = data.get('age', 'Any')
        gender = data.get('gender', 'All')
        persona = data.get('persona', '')
        length = data.get('length', 'Medium')
        category = data.get('category', 'Awareness')
        language = data.get('language', 'Myanglish')
        ai_model = data.get('ai_model', 'Gemini 2.5 Flash')
        
        # Refinement
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

        # Prompt Building
        prompt = ""
        if refine_instruction and current_text:
            prompt = f"""
            Act as an Editor.
            Original: "{current_text}"
            Task: Rewrite based on: "{refine_instruction}"
            Keep style: {language}.
            Output JSON with key: "post_content".
            """
        else:
            prompt = f"""
            Act as Social Media Manager.
            Platform: {platform}
            Topic: {topic}
            Audience: {gender}, {age} ({persona})
            Goal: {category}
            Tone: {tone}
            Length: {length}
            Language: {language}
            
            Formatting: Use line breaks and bold text.
            Output JSON with key: "post_content".
            """

        # Generate
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

# --- ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def home():
    # Indentation ကို သေချာ ပြင်ထားပေးပါတယ်
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
