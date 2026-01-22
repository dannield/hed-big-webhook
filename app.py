from flask import Flask, request, jsonify, redirect, render_template_string
import requests
import os
import secrets
import time

app = Flask(__name__)

# HED-BIG credentials
HED_BIG_EMAIL = os.environ.get('HED_BIG_EMAIL', 'Floor14@final.co.il')
HED_BIG_PASSWORD = os.environ.get('HED_BIG_PASSWORD', 'Aa@000014')
HED_BIG_BASE_URL = 'https://hed-big.web.app'

# OAuth configuration
OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID', 'hed-big-client-id')
OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET', secrets.token_urlsafe(32))

# Simple in-memory token storage (in production, use a database)
tokens = {}
auth_codes = {}

# Simple OAuth authorization page HTML
AUTH_PAGE_HTML = '''
<!DOCTYPE html>
<html>
<head><title>HED-BIG Authorization</title></head>
<body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
<h1>Authorize HED-BIG Blinds Control</h1>
<p>Google Home wants to control your HED-BIG blinds.</p>
<form method="POST">
<button type="submit" name="authorize" style="padding: 10px 20px; background: #4285f4; color: white; border: none; border-radius: 4px; cursor: pointer;">Authorize</button>
</form>
</body>
</html>
'''

@app.route('/oauth/authorize', methods=['GET', 'POST'])
def oauth_authorize():
    if request.method == 'POST':
        # Generate authorization code
        code = secrets.token_urlsafe(32)
        state = request.args.get('state', '')
        redirect_uri = request.args.get('redirect_uri')
        
        # Store the code temporarily
        auth_codes[code] = {
            'client_id': request.args.get('client_id'),
            'timestamp': time.time()
        }
        
        # Redirect back to Google with the code
        return redirect(f"{redirect_uri}?code={code}&state={state}")
    
    # Show authorization page
    return render_template_string(AUTH_PAGE_HTML)

@app.route('/oauth/token', methods=['POST'])
def oauth_token():
    try:
        grant_type = request.form.get('grant_type')
        
        if grant_type == 'authorization_code':
            code = request.form.get('code')
            
            # Verify the authorization code
            if code not in auth_codes:
                return jsonify({'error': 'invalid_grant'}), 400
            
            # Clean up old code
            del auth_codes[code]
            
            # Generate access and refresh tokens
            access_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            
            # Store tokens
            tokens[access_token] = {
                'refresh_token': refresh_token,
                'timestamp': time.time()
            }
            
            return jsonify({
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'refresh_token': refresh_token
            })
        
        elif grant_type == 'refresh_token':
            # Handle token refresh
            refresh_token = request.form.get('refresh_token')
            
            # Find the access token by refresh token
            for access_token, data in tokens.items():
                if data.get('refresh_token') == refresh_token:
                    # Generate new access token
                    new_access_token = secrets.token_urlsafe(32)
                    tokens[new_access_token] = data
                    del tokens[access_token]
                    
                    return jsonify({
                        'access_token': new_access_token,
                        'token_type': 'Bearer',
                        'expires_in': 3600
                    })
            
            return jsonify({'error': 'invalid_grant'}), 400
        
        return jsonify({'error': 'unsupported_grant_type'}), 400
    
    except Exception as e:
        print(f"Token error: {str(e)}")
        return jsonify({'error': 'server_error'}), 500

@app.route('/fulfillment', methods=['POST'])
def fulfillment():
    """Google Home Smart Home fulfillment endpoint"""
    try:
        data = request.json
        intent = data.get('inputs', [{}])[0].get('intent')
        request_id = data.get('requestId')
        
        print(f"Received intent: {intent}")
        
        if intent == 'action.devices.SYNC':
            # Return available devices
            return jsonify({
                'requestId': request_id,
                'payload': {
                    'agentUserId': 'hed-big-user',
                    'devices': [
                        {
                            'id': 'DO-IT-NETWORK1-9',
                            'type': 'action.devices.types.BLINDS',
                            'traits': ['action.devices.traits.OpenClose'],
                            'name': {
                                'name': 'Living Room Blinds'
                            },
                            'willReportState': False
                        }
                    ]
                }
            })
        
        elif intent == 'action.devices.QUERY':
            # Return device states
            devices = data.get('inputs', [{}])[0].get('payload', {}).get('devices', [])
            device_states = {}
            
            for device in devices:
                device_states[device['id']] = {
                    'online': True,
                    'openPercent': 0
                }
            
            return jsonify({
                'requestId': request_id,
                'payload': {
                    'devices': device_states
                }
            })
        
        elif intent == 'action.devices.EXECUTE':
            # Execute commands
            commands = data.get('inputs', [{}])[0].get('payload', {}).get('commands', [])
            command_results = []
            
            for command in commands:
                for device in command.get('devices', []):
                    device_id = device['id']
                    
                    for execution in command.get('execution', []):
                        cmd = execution['command']
                        params = execution.get('params', {})
                        
                        # TODO: Implement actual HED-BIG control
                        print(f"Would execute {cmd} on {device_id} with params {params}")
                        
                        command_results.append({
                            'ids': [device_id],
                            'status': 'SUCCESS',
                            'states': {
                                'online': True,
                                'openPercent': params.get('openPercent', 0)
                            }
                        })
            
            return jsonify({
                'requestId': request_id,
                'payload': {
                    'commands': command_results
                }
            })
        
        elif intent == 'action.devices.DISCONNECT':
            # Handle account unlinking
            return jsonify({})
        
        return jsonify({'error': 'unsupported_intent'}), 400
    
    except Exception as e:
        print(f"Fulfillment error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"OAuth Client ID: {OAUTH_CLIENT_ID}")
    print(f"OAuth Client Secret: {OAUTH_CLIENT_SECRET}")
    app.run(host='0.0.0.0', port=port)
