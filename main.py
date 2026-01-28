import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import uuid
import os
import json

# --- 🔒 การเชื่อมต่อ Firebase แบบปลอดภัย ---
try:
    # พยายามอ่านค่าจาก Environment Variable (สำหรับ Render.com)
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    
    if firebase_config_str:
        # ถ้าเจอค่าในระบบ ให้แปลงจาก String เป็น JSON
        firebase_config_dict = json.loads(firebase_config_str)
        cred = credentials.Certificate(firebase_config_dict)
    else:
        # ถ้าไม่เจอ (เช่น รันในเครื่องตัวเอง) ให้ลองอ่านจากไฟล์เดิม
        cred = credentials.Certificate("firebase-key.json")

    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://minecityimages-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })
    print("✅ Firebase Connected!")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50))
        
        pixels = []
        width, height = img.size
        
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        ref = db.reference(f'images/{image_id}')
        ref.set({
            "data": pixels,
            "width": width,
            "height": height
        })
        
        return jsonify({"id": image_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City API is Running!"

if __name__ == '__main__':
    # สำหรับ Render.com ต้องดึงค่า Port จากระบบ หรือใช้ 5000 เป็นค่าเริ่มต้น
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Mine City API is starting on port {port}...")
    app.run(host='0.0.0.0', port=port)

