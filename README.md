# Store Assistant

A web-based inventory management system with an AI-powered chatbot assistant that helps manage store inventory through text and voice interactions.

## Features

- 🤖 AI-powered chatbot for inventory management
- 🎤 Voice input support
- 📝 Text-based chat interface
- 📦 Real-time inventory tracking
- 🔐 User authentication
- 📱 Responsive design

## Tech Stack

- **Frontend:**
  - HTML5
  - CSS3
  - JavaScript (Vanilla)
  - Material Icons

- **Backend:**
  - Python
  - Flask
  - Firebase (Firestore)
  - Groq LLM API
  - Whisper (Speech-to-Text)

## Prerequisites

- Python 3.8+
- Node.js (for development)
- Firebase account
- Groq API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd store-assistant
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
GROQ_API_KEY=your_groq_api_key
```

4. Set up Firebase:
- Create a new Firebase project
- Download your Firebase credentials JSON file
- Rename it to `firebase-credentials.json` and place it in the root directory

## Project Structure

```
store-assistant/
├── pages/
│   └── chatbot.html
├── static/
│   ├── css/
│   └── js/
│       └── script.js
├── chat_api.py
├── chat_service.py
├── voice_service.py
├── firebase_config.py
├── requirements.txt
└── README.md
```

## Running the Application

1. Start the Flask server:
```bash
python chat_api.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Features in Detail

### Chat Interface
- Real-time text-based communication
- Message history
- Loading states for better UX
- Error handling and recovery

### Voice Input
- Browser-based speech recognition
- Support for multiple languages
- Real-time voice-to-text conversion
- Fallback for unsupported browsers

### Inventory Management
- View current inventory levels
- Add new items
- Update existing items
- Generate inventory reports
- Search functionality

## API Endpoints

- `POST /api/chat` - Process text-based queries
- `POST /api/voice` - Process voice input
- `GET /api/inventory/summary` - Get inventory summary

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI Whisper for speech recognition
- Groq for LLM capabilities
- Firebase for database management
- Material Icons for UI elements
