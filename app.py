import os
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "mysecretkey123")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "12345")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, age, gender, persona, length, category):
    model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
    
    # Construct Audience Profile
    audience_profile = f"{gender} audience, aged {age}"
    if persona:
        audience_profile += f", who are specifically {persona}"

    # Length Logic
    length_instruction = "standard length (100-150 words)"
    if length == "Short": length_instruction = "very short (under 50 words)"
    elif length == "Long": length_instruction = "long-form (over 200 words)"

    # Category Logic
    category_instruction = "General social media post"
    if category == "Brand Awareness":
        category_instruction = "Focus on storytelling, brand identity. No hard selling."
    elif category == "Engagement":
        category_instruction = "Focus on interaction. Ask questions, polls, encourage tagging."
    elif category == "Educational":
        category_instruction = "Focus on value. Teach something new, share tips, or how-to guides."
    elif category == "Copywriting":
        category_instruction = "Focus on sales. Use persuasion (PAS/AIDA). Strong Call to Action."

    prompt = f"""
    Act as a Senior Social Media Manager.
    Create a post for {platform}.
    
    Target Audience Profile: {audience_profile}
    Topic: {topic}
    Content Goal: {category} ({category_instruction})
    Tone: {tone}
    Length: {length_instruction}

    Instructions:
    1. Adapt the language style to fit the age group and gender (e.g., use slang for youth, formal for professionals).
    2. Write in Burmese (Myanmar) mixed with English naturally.
    3. Use Markdown formatting.

    Output JSON:
    {{
        "post_content": "The caption content...",
        "image_prompt": "Detailed image description in English..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"post_content": f"Error: {str(e)}", "image_prompt": ""}

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
        data.get('topic'), 
        data.get('platform'), 
        data.get('tone'),
        data.get('age'),       # New
        data.get('gender'),    # New
        data.get('persona'),   # Renamed from 'audience' input
        data.get('length'),
        data.get('category') 
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
