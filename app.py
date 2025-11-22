from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# သင့် API Key ကို ဒီမှာထည့်ပါ
import os
# API Key ကို Server ကနေ ယူမယ့် ပုံစံပါ
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_content(topic, platform, tone, audience):
    # သင်စမ်းသပ်ပြီး အဆင်ပြေခဲ့သော Model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Prompt ကို ပိုကောင်းအောင် (Engineering) လုပ်ထားခြင်း
    prompt = f"""
    Act as a professional Social Media Manager for the Myanmar market.
    Create a high-engagement post for {platform}.
    
    Here are the details:
    - Topic: {topic}
    - Target Audience: {audience}
    - Tone: {tone}
    
    Instructions:
    1. Start with a 'Hook' (First sentence must grab attention).
    2. Use natural Burmese (Myanmar) language mixed with English words where appropriate (Burmese-English style).
    3. Structure the content clearly with line breaks.
    4. End with a strong Call to Action (CTA).
    5. Add 5-10 relevant and trending hashtags.
    6. Use emojis to make it lively.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get('topic')
    platform = data.get('platform')
    tone = data.get('tone')
    audience = data.get('audience') # အသစ်ထပ်ဖြည့်ထားသည်

    if not topic:
        return jsonify({'result': 'ခေါင်းစဉ်ထည့်ရန် လိုအပ်ပါသည်'}), 400

    content = generate_content(topic, platform, tone, audience)
    return jsonify({'result': content})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
