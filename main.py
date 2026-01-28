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
        # รับค่า CitizenID จากหน้าเว็บ
        citizen_id_input = request.form.get('userId')
        
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # 1. ประมวลผลรูปภาพ 50x50 พิกเซล
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((50, 50))
        
        pixels = []
        for y in range(50):
            for x in range(50):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
                
        image_id = str(uuid.uuid4())[:8]
        
        # 2. บันทึกข้อมูลพิกเซลลง images/ (เพื่อให้ Roblox ดึงไปวาด)
        db.reference(f'images/{image_id}').set({
            "data": pixels,
            "width": 50,
            "height": 50
        })

        # 3. ระบบค้นหาเป้าหมาย (Manual Mapping & Type Conversion)
        if citizen_id_input:
            try:
                # แปลงค่าที่กรอกมาให้เป็นตัวเลข เพื่อให้ตรงกับ Firebase
                search_target = int(str(citizen_id_input).strip())
                print(f"🔎 กำลังค้นหา CitizenID (Number): {search_target}")
                
                users_ref = db.reference('UsersID')
                all_users = users_ref.get() # ดึงข้อมูล UsersID ทั้งหมด

                target_roblox_id = None
                if all_users:
                    for roblox_id, user_info in all_users.items():
                        # ดึง CitizenID จาก DB มาเทียบแบบตัวเลข
                        db_val = user_info.get('CitizenID')
                        if db_val == search_target:
                            target_roblox_id = roblox_id
                            break
                
                if target_roblox_id:
                    # อัปเดต ImageURL ในตำแหน่งที่พบข้อมูลผู้เล่น
                    db.reference(f'UsersID/{target_roblox_id}').update({
                        "ImageURL": image_id
                    })
                    print(f"✅ สำเร็จ! เปลี่ยนรูปให้ {target_roblox_id}")
                    return jsonify({"success": True, "id": image_id})
                else:
                    # หากหาเลขไม่เจอ (เป็นที่มาของ Log 200 18)
                    print(f"⚠️ หาไม่พบเลข {search_target} ในฐานข้อมูล")
                    return jsonify({"error": "ID not found"}), 404
                    
            except ValueError:
                return jsonify({"error": "Invalid ID format"}), 400
        
        return jsonify({"success": True, "id": image_id})

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Mine City API is Running!"

if __name__ == '__main__':
    # กำหนด Port สำหรับ Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
