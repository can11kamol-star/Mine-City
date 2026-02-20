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

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://minecityimages-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
    print("✅ Firebase Connected!")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

app = Flask(__name__)
CORS(app)

# --- 🖼️ ระบบอัปโหลดรูปภาพ ---
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img = img.resize((100, 100))
        
        pixels = []
        for y in range(100):
            for x in range(100):
                r, g, b = img.getpixel((x, y))
                pixels.append([r, g, b])
        
        image_id = str(uuid.uuid4())[:8]
        
        db.reference(f'images/{image_id}').set({
            "data": pixels, 
            "width": 100, 
            "height": 100
        })
        
        print(f"✅ บันทึกรูปภาพสำเร็จ ID: {image_id}")
        return jsonify({"success": True, "id": image_id})
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- 💾 ระบบบันทึกข้อมูลผู้เล่น (เพิ่มระบบเซฟรถ Vehicles) ---
@app.route('/save_player_data', methods=['POST'])
def save_player_data():
    try:
        data = request.json
        user_id = str(data.get('userId'))
        if not user_id:
            return jsonify({"error": "No userId"}), 400

        job_title = data.get('job', 'Citizen')
        
        # ✅ ดึงข้อมูลรายชื่อรถจากที่ส่งมา (ถ้าไม่มีให้เป็น List ว่าง)
        owned_vehicles = data.get('vehicles', [])

        # ✅ อัปเดตข้อมูลลง Firebase (เพิ่มฟิลด์ vehicles)
        ref = db.reference(f'UsersID/{user_id}')
        ref.update({
            'InGameName': data.get('username'),
            'money': data.get('money'),
            'bank': data.get('bank'),
            'job': job_title,
            'Inventory': data.get('inventory'),
            'vehicles': owned_vehicles,          # 🚗 เก็บรายชื่อรถที่ซื้อแล้ว
            'jailTime': data.get('jailTime', 0), # ⚖️ เก็บเวลาติดคุก (เผื่อไว้)
            'LastSave': {".sv": "timestamp"}
        })
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"❌ Save Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# --- 📂 ระบบโหลดข้อมูลผู้เล่น ---
@app.route('/get_player_data/<user_id>', methods=['GET'])
def get_player_data(user_id):
    try:
        ref = db.reference(f'UsersID/{user_id}')
        data = ref.get()
        if data:
            # 🛡️ ตรวจสอบว่าถ้าใน DB ไม่มีฟิลด์ vehicles ให้ส่ง List ว่างกลับไปแทน
            if 'vehicles' not in data:
                data['vehicles'] = []
            return jsonify(data), 200
        
        return jsonify({"status": "not_found"}), 404
    except Exception as e:
        print(f"❌ Load Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
