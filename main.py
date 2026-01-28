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
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        # รับค่า CitizenID จากหน้าเว็บ
        citizen_id_input = request.form.get('userId') 
        
        # 1. ประมวลผลรูปภาพ 50x50
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50)) 
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        
        # 2. บันทึกข้อมูลพิกเซลลง images/
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })
        
        # 3. ระบบค้นหาและอัปเดต (ปรับปรุงใหม่ให้แม่นยำ 100%)
        status_msg = "Image generated"
        if citizen_id_input and citizen_id_input.strip() != "":
            search_id = str(citizen_id_input).strip()
            print(f"🔎 กำลังค้นหา CitizenID: '{search_id}' ในฐานข้อมูล...")
            
            users_ref = db.reference('UsersID')
            all_users = users_ref.get() # ดึงข้อมูลผู้เล่นทั้งหมด
            
            target_roblox_id = None
            if all_users:
                for roblox_id, data in all_users.items():
                    # ดึงค่า CitizenID จาก Firebase และแปลงเป็น String เพื่อป้องกันปัญหาประเภทข้อมูล
                    db_citizen_id = str(data.get('CitizenID', '')).strip()
                    
                    if db_citizen_id == search_id:
                        target_roblox_id = roblox_id
                        break
            
            if target_roblox_id:
                # ถ้าเจอ ให้เข้าไปเขียนทับ ImageURL
                db.reference(f'UsersID/{target_roblox_id}').update({
                    "ImageURL": image_id
                })
                status_msg = f"Successfully updated ImageURL for CitizenID: {search_id}"
                print(f"✅ สำเร็จ! อัปเดตรูปให้ RobloxID: {target_roblox_id}")
            else:
                error_log = f"ไม่พบเลขบัตร '{search_id}' ในโฟลเดอร์ UsersID"
                print(f"⚠️ {error_log}")
                return jsonify({"error": error_log}), 404
        
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
