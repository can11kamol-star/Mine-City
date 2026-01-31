import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
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
    print("✅ API is Ready for Mine City Processing")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

app = Flask(__name__)
CORS(app)

# --- 💾 ระบบบันทึกข้อมูลผู้เล่น (ลง UsersID) ---
@app.route('/save_player_data', methods=['POST'])
def save_player_data():
    try:
        data = request.json
        user_id = str(data.get('userId'))
        if not user_id:
            return jsonify({"error": "No userId"}), 400

        # ✅ บันทึกลง UsersID เพื่อให้รวมกับข้อมูลบัตรประชาชนเดิมของคุณ
        ref = db.reference(f'UsersID/{user_id}')
        
        # ✅ ใช้ update เพื่อเพิ่ม Money โดยไม่ลบข้อมูล Bio/Gender เดิม
        ref.update({
            'InGameName': data.get('username'),
            'Money': data.get('money'),
            'Inventory': data.get('inventory'),
            'LastUpdate': {".sv": "timestamp"}
        })
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error saving data: {e}")
        return jsonify({"error": str(e)}), 500

# --- 📂 ระบบโหลดข้อมูลผู้เล่น ---
@app.route('/get_player_data/<user_id>', methods=['GET'])
def get_player_data(user_id):
    try:
        ref = db.reference(f'UsersID/{user_id}')
        data = ref.get()
        if data:
            return jsonify(data), 200
        return jsonify({"status": "not_found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
