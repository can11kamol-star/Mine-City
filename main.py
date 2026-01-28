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
        # 1. ตรวจสอบไฟล์รูปภาพ
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        # รับค่าจากหน้าเว็บ (ซึ่งตอนนี้คือ CitizenID เช่น 378901)
        citizen_id_input = request.form.get('userId') 
        
        # 2. ประมวลผลรูปภาพ (50x50 พิกเซล)
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50)) 
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        # 3. สร้างรหัสรูปภาพ 8 หลัก
        image_id = str(uuid.uuid4())[:8]
        
        # 4. บันทึกข้อมูลพิกเซลลง images/
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })
        
        # 5. ระบบค้นหา UserId จาก CitizenID เพื่ออัปเดตรูป
        status_msg = "Image generated"
        if citizen_id_input and citizen_id_input.strip() != "":
            users_ref = db.reference('UsersID')
            all_users = users_ref.get() # ดึงข้อมูลผู้เล่นทั้งหมดมาค้นหา
            
            target_roblox_id = None
            if all_users:
                for roblox_id, data in all_users.items():
                    # ตรวจสอบว่า CitizenID ใน Firebase ตรงกับที่กรอกมาหรือไม่
                    if str(data.get('CitizenID')) == str(citizen_id_input).strip():
                        target_roblox_id = roblox_id
                        break
            
            if target_roblox_id:
                # ถ้าเจอ ให้เข้าไปอัปเดต ImageURL ในโฟลเดอร์ UserId นั้นๆ
                db.reference(f'UsersID/{target_roblox_id}').update({
                    "ImageURL": image_id
                })
                status_msg = f"Successfully updated ImageURL for CitizenID: {citizen_id_input}"
                print(f"✅ {status_msg} (RobloxID: {target_roblox_id})")
            else:
                status_msg = f"CitizenID {citizen_id_input} not found in database"
                print(f"⚠️ {status_msg}")
                return jsonify({"error": status_msg}), 404
        
        return jsonify({
            "success": True, 
            "id": image_id, 
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
    app.run(host='0.0.0.0', port=port)
