import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import uuid
import os
import json

# --- 🔒 การเชื่อมต่อ Firebase ---
try:
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    if firebase_config_str:
        firebase_config_dict = json.loads(firebase_config_str)
        cred = credentials.Certificate(firebase_config_dict)
    else:
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
        # 1. ประมวลผลรูปภาพ 50x50 พิกเซล
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
            
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50))
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        
        # 2. บันทึกพิกเซลลง images/ (เพื่อให้ Roblox ดึงไปวาด)
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })

        # 3. วิธีแก้แบบใหม่: เจาะจงไปที่ RobloxID ของคุณโดยตรง (ไม่ต้องวนลูปหา)
        # เราจะลองเปลี่ยนรูปให้ RobloxID: 9232519691 ซึ่งมี CitizenID: 378901
        target_path = 'UsersID/9232519691' 
        
        db.reference(target_path).update({
            "ImageURL": image_id
        })
        
        print(f"🚀 [DIRECT UPDATE] เปลี่ยน ImageURL เป็น {image_id} สำเร็จ!")
        return jsonify({"success": True, "id": image_id, "path_updated": target_path})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City Direct-API is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
