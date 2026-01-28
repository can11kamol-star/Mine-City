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
        # รับค่า CitizenID จากหน้าเว็บ (เช่น 378901)
        citizen_id_input = request.form.get('userId')
        
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # 1. ประมวลผลรูปภาพ 50x50 เพื่อความเสถียร
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50))
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        
        # 2. บันทึกข้อมูลพิกเซลลง images/ เพื่อให้ Roblox ดึงไปวาด
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })

        # 3. ระบบค้นหาและอัปเดตเจาะจงโครงสร้าง UsersID
        status_msg = "Image generated"
        if citizen_id_input:
            search_target = str(citizen_id_input).strip()
            users_ref = db.reference('UsersID')
            all_users = users_ref.get() # ดึงข้อมูลทั้งหมดภายใต้ UsersID

            found_roblox_id = None
            if all_users:
                # วนลูปหาในทุกๆ RobloxID
                for roblox_id, data in all_users.items():
                    # ตรวจสอบว่า CitizenID ใน Firebase ตรงกับที่กรอกมาหรือไม่
                    if data and str(data.get('CitizenID')) == search_target:
                        found_roblox_id = roblox_id
                        break
            
            if found_roblox_id:
                # ถ้าเจอ ให้อัปเดต ImageURL ในโฟลเดอร์ RobloxID นั้น
                db.reference(f'UsersID/{found_roblox_id}').update({
                    "ImageURL": image_id
                })
                print(f"✅ สำเร็จ! อัปเดต ImageURL ให้ {found_roblox_id} (CitizenID: {search_target})")
                return jsonify({"success": True, "id": image_id})
            else:
                # นี่คือจุดที่ทำให้เกิดเลข 18 ใน Log เพราะหาเลขบัตรไม่เจอ
                error_msg = f"ไม่พบ CitizenID: {search_target}"
                print(f"⚠️ {error_msg}")
                return jsonify({"error": error_msg}), 404
        
        return jsonify({"success": True, "id": image_id})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City API is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
