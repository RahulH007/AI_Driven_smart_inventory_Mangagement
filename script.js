// Page Management
function showPage(pageId) {
    // Hide all content pages
    document.querySelectorAll('.content-page').forEach(page => {
        page.style.display = 'none';
    });
    
    // Show selected page
    document.getElementById(`${pageId}-page`).style.display = 'block';
}

// Authentication
function handleAuth(action) {
    const storeName = document.getElementById('store-name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!storeName || !email || !password) {
        alert('Please fill in all fields');
        return;
    }

    // In a real app, this would make an API call
    document.getElementById('auth-section').classList.remove('active');
    document.getElementById('app-section').classList.add('active');
    showPage('inventory'); // Show inventory page by default after login
}

function logout() {
    document.getElementById('app-section').classList.remove('active');
    document.getElementById('auth-section').classList.add('active');
    
    // Clear form fields
    document.getElementById('store-name').value = '';
    document.getElementById('email').value = '';
    document.getElementById('password').value = '';
}

// Camera handling for barcode scanner
async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        const videoElement = document.getElementById('camera-feed');
        videoElement.srcObject = stream;
    } catch (error) {
        console.error('Error accessing camera:', error);
        alert('Could not access camera. Please make sure you have granted camera permissions.');
    }
}

// Voice input for chatbot
let isRecording = false;
const voiceBtn = document.querySelector('.voice-btn');

voiceBtn.addEventListener('click', () => {
    if (!isRecording) {
        startVoiceRecording();
    } else {
        stopVoiceRecording();
    }
    isRecording = !isRecording;
    voiceBtn.querySelector('.material-icons').textContent = isRecording ? 'stop' : 'mic';
});

function startVoiceRecording() {
    // In a real app, this would initialize the Web Speech API
    console.log('Started recording...');
}

function stopVoiceRecording() {
    // In a real app, this would stop recording and process the audio
    console.log('Stopped recording');
}

// Send chat message
document.querySelector('.send-btn').addEventListener('click', () => {
    const input = document.querySelector('.chat-input input');
    const message = input.value.trim();
    
    if (message) {
        addChatMessage(message, 'user');
        // In a real app, this would send the message to a backend
        setTimeout(() => {
            addChatMessage('I received your message. How can I help?', 'bot');
        }, 1000);
        input.value = '';
    }
});

function addChatMessage(text, sender) {
    const messagesContainer = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    // Show auth section by default
    document.getElementById('auth-section').classList.add('active');
});