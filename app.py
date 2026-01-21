from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# HED-BIG credentials
HED_BIG_EMAIL = os.environ.get('HED_BIG_EMAIL', 'Floor14@final.co.il')
HED_BIG_PASSWORD = os.environ.get('HED_BIG_PASSWORD', 'Aa@000014')
HED_BIG_BASE_URL = 'https://hed-big.web.app'

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        action = data.get('action', '')
        device_id = data.get('device_id', '')
        
        # Log the incoming request
        print(f"Received action: {action}, device_id: {device_id}")
        
        # TODO: Implement HED-BIG control logic
        # This will need to:
        # 1. Login to HED-BIG
        # 2. Send control commands to the specified device
        # 3. Return success/failure
        
        return jsonify({
            'status': 'success',
            'message': f'Action {action} triggered for device {device_id}'
        }), 200
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
