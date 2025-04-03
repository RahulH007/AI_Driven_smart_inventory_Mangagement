from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
import asyncio
from voice_service import VoiceProcessingService
import io
import base64
import cv2
import numpy as np
from pyzbar.pyzbar import decode

# Add parent directory to path for imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix imports to use modules in the current directory
from chat_service import InventoryChatService, ChatService

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize chat service
chat_service = InventoryChatService()

# Initialize voice service after initializing chat service
voice_service = VoiceProcessingService(chat_service)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API endpoint to process chat queries
    """
    data = request.json
    user_query = data.get('query', '')
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Process the query using the chat service
        response = asyncio.run(chat_service.process_query(user_query))
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/inventory/summary', methods=['GET'])
def inventory_summary():
    """
    API endpoint to get inventory summary
    """
    try:
        summary = asyncio.run(chat_service.get_inventory_summary())
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/voice', methods=['POST'])
def voice_query():
    """
    API endpoint to process voice queries
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    
    try:
        # Read audio data
        audio_data = audio_file.read()
        
        # Process the voice query
        response = asyncio.run(voice_service.process_voice_query(audio_data))
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/barcode/scan', methods=['POST'])
def scan_barcode():
    """
    API endpoint to scan barcodes from images
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    
    try:
        # Read image data
        image_bytes = image_file.read()
        
        # Convert to numpy array for OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Try to decode barcodes
        barcodes = decode(img)
        
        if not barcodes:
            return jsonify({"error": "No barcode detected"}), 404
        
        # Get the first barcode
        barcode = barcodes[0]
        barcode_data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        
        return jsonify({
            "barcode": barcode_data,
            "type": barcode_type
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))