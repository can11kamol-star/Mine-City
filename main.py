import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import uuid
import os
import json

# --- 🔒 การเชื่อมต่อ Firebase (URL ปรับปรุงตามที่คุณส่งมา) ---
try:
    firebase_config_str = os.getenv('FIREBASE_CONFIG')
    if firebase_config_str:
        firebase_config_dict = json.loads(firebase_config_str)
        cred = credentials.Certificate(firebase_config_dict)
    else:
        cred = credentials.Certificate("firebase-key.json")

    # ตรวจสอบว่ามีการ Initialize ไปหรือยังเพื่อป้องกัน Error
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://minecityimages-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    print("✅ Firebase Connected to: minecityimages-default-rtdb")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        citizen_id_input = request.form.get('userId')
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # 1. ประมวลผลรูป 50x50
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50))
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
        
        image_id = str(uuid.uuid4())[:8]

        # 2. บันทึกพิกเซล
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })

        # 3. ระบบค้นหาเป้าหมาย (Manual Loop เพื่อแก้ปัญหา Type Mismatch)
        if citizen_id_input:
            search_target = str(citizen_id_input).strip()
            users_ref = db.reference('UsersID')
            all_users = users_ref.get()

            # DEBUG: Print ข้อมูลที่ดึงได้ลง Log เพื่อเช็คการเชื่อมต่อ
            print(f"🔎 ค้นหา CitizenID: {search_target} | ข้อมูลใน DB: {all_users}")

            target_roblox_id = None
            if all_users:
                for roblox_id, user_data in all_users.items():
                    # เทียบค่าแบบ String ทั้งคู่
                    if str(user_data.get('CitizenID')) == search_target:
                        target_roblox_id = roblox_id
                        break
            
            if target_roblox_id:
                # สั่งเขียนข้อมูลทับ ImageURL
                db.reference(f'UsersID/{target_roblox_id}').update({
                    "ImageURL": image_id
                })
                return jsonify({"success": True, "id": image_id, "updated": target_roblox_id})
            
            return jsonify({"error": "ID not found in database"}), 404
            
        return jsonify({"success": True, "id": image_id})

    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
