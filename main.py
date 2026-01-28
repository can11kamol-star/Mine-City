import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import uuid
import os
import json

# --- 🔒 เชื่อมต่อ Firebase ---
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
        # 1. รับค่า CitizenID จากหน้าเว็บ (เช่น 378901)
        citizen_id_input = request.form.get('userId') 
        print(f"🔎 เริ่มการค้นหาสำหรับ CitizenID: '{citizen_id_input}'")
        
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # 2. ประมวลผลรูป 50x50
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50)) 
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        
        # 3. บันทึกข้อมูลพิกเซลลง images/
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })

        # 4. ค้นหาและอัปเดต ImageURL (ปรับปรุงใหม่)
        if citizen_id_input and citizen_id_input.strip() != "":
            target_id = str(citizen_id_input).strip()
            users_ref = db.reference('UsersID')
            all_users = users_ref.get() # ดึงข้อมูลทั้งหมดใน UsersID

            found_roblox_id = None
            if all_users:
                for roblox_id, data in all_users.items():
                    # แปลงค่า CitizenID จาก DB เป็น String เพื่อป้องกันปัญหา Type mismatch
                    db_citizen_id = str(data.get('CitizenID', '')).strip()
                    
                    if db_citizen_id == target_id:
                        found_roblox_id = roblox_id
                        break
            
            if found_roblox_id:
                # อัปเดต ImageURL เข้าไปที่ RobloxID ที่เจอ
                db.reference(f'UsersID/{found_roblox_id}').update({
                    "ImageURL": image_id
                })
                print(f"✅ สำเร็จ! อัปเดต ImageURL ให้ {found_roblox_id} (CitizenID: {target_id})")
                return jsonify({"success": True, "id": image_id})
            else:
                print(f"⚠️ ไม่พบ CitizenID: {target_id} ในฐานข้อมูล")
                return jsonify({"error": f"ไม่พบเลขบัตร {target_id} ในระบบ"}), 404
        
        return jsonify({"success": True, "id": image_id, "note": "image only"})

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City API is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
