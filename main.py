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
    # สำหรับ Render.com จะดึงค่าจาก Environment Variable
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    
    if firebase_config_str:
        firebase_config_dict = json.loads(firebase_config_str)
        cred = credentials.Certificate(firebase_config_dict)
    else:
        # สำหรับรันในเครื่องตัวเอง
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
        # 1. ตรวจสอบไฟล์รูปภาพ
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        # รับค่า UserId จากหน้าเว็บ (จะได้รับเฉพาะเมื่อกดปุ่มที่ 2)
        user_id = request.form.get('userId') 
        
        # 2. ประมวลผลรูปภาพ (ใช้ 50x50 เพื่อความเสถียรของระบบวาดพิกเซล)
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50)) 
        
        pixels = []
        width, height = img.size
        
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        # 3. สร้างรหัสรูปภาพ 8 หลัก
        image_id = str(uuid.uuid4())[:8]
        
        # 4. บันทึกพิกเซลลงในโฟลเดอร์ images/ (เก็บไว้ดึงข้อมูลไปวาดใน Roblox)
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": width,
            "height": height
        })
        
        # 5. ตรวจสอบและอัปเดตข้อมูลผู้เล่น (ImageURL) ✨
        status_msg = "Image created successfully"
        if user_id and user_id.strip() != "":
            # อัปเดต ImageURL ใน UsersID/[userId] ทันที
            db.reference(f'UsersID/{user_id}').update({
                "ImageURL": image_id
            })
            status_msg = f"Updated ImageURL for user {user_id}"
            print(f"✅ {status_msg}")
        else:
            print(f"ℹ️ Image generated without userId: {image_id}")
        
        return jsonify({
            "success": True, 
            "id": image_id, 
            "userId": user_id,
            "status": status_msg
        })
        
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City API is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Mine City API is starting on port {port}...")
    app.run(host='0.0.0.0', port=port)
