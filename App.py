from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

# Use the PORT environment variable that Render automatically provides
port = int(os.environ.get('PORT', 10000))

# Your keystream link. Using your 'speedtest3' domain which you confirmed works.
keystream_url = 'http://speedtest3.tedata.net.prod.hosts.ooklaserver.net:8080/download?size=70000000'

print("Starting keystream download from:", keystream_url)
KEYSTREAM = b''
try:
    r = requests.get(keystream_url, stream=True)
    for chunk in r.iter_content(chunk_size=65536):
        KEYSTREAM += chunk
        if len(KEYSTREAM) >= 70000000:
            break
    print(f"Success! Keystream downloaded: {len(KEYSTREAM)} bytes")
except Exception as e:
    print(f"Error downloading keystream: {e}")
    KEYSTREAM = b'\x00' * 70000000 # fallback
    print("Using fallback null keystream")

def xor_with_keystream(data, offset=0):
    if not KEYSTREAM:
        return data
    result = bytearray()
    for i, b in enumerate(data):
        ks = KEYSTREAM[(offset + i) % len(KEYSTREAM)]
        result.append(b ^ ks)
    return bytes(result)

@app.route('/tunnel')
def tunnel():
    target = request.args.get('url')
    if not target:
        return "Missing url parameter", 400
    
    # Verify protocol. The requests library needs http:// or https://
    if not target.startswith('http'):
        target = 'http://' + target
        
    try:
        resp = requests.get(target, timeout=10)
        # Ensure the content is bytes
        content = resp.content if isinstance(resp.content, bytes) else resp.content.encode('utf-8')
        encoded = xor_with_keystream(content)
        # Return as binary data
        return Response(encoded, mimetype='application/octet-stream')
    except Exception as e:
        return f"Error fetching target: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)
