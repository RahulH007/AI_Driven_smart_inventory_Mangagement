import requests
import os
import argparse
import sys
import tempfile
import threading
import time
import wave
import pyaudio
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QLabel, QTextEdit, QWidget, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AudioRecorder(QThread):
    """Thread for recording audio without blocking the UI"""
    update_status = pyqtSignal(str)
    update_level = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.audio_file_path = None
        
    def run(self):
        """Record audio until stopped"""
        # Audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        
        # Create temp file for audio data
        fd, self.audio_file_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Open stream
        try:
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            self.update_status.emit("Recording started... Tell your query")
            self.is_recording = True
            
            # Start recording
            frames = []
            while self.is_recording:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Update audio level indicator (simple implementation)
                try:
                    audio_level = min(100, int(max(abs(int.from_bytes(data[:2], byteorder='little', signed=True)) 
                                             for _ in range(10)) / 300))
                    self.update_level.emit(audio_level)
                except:
                    pass
                
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            self.update_status.emit("Recording stopped, processing...")
            
            # Save the audio file
            with wave.open(self.audio_file_path, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                
            self.update_status.emit(f"Audio saved to {self.audio_file_path}")
            
        except Exception as e:
            self.update_status.emit(f"Error recording audio: {str(e)}")
            self.is_recording = False
    
    def stop(self):
        """Stop the recording"""
        self.is_recording = False

class VoiceQueryApp(QMainWindow):
    """GUI application for voice querying the inventory system"""
    
    def __init__(self):
        super().__init__()
        self.recorder = None
        self.server_url = "http://localhost:5000/api/voice"
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        # Main window setup
        self.setWindowTitle("Voice Query Inventory Assistant")
        self.setGeometry(300, 300, 600, 500)
        
        # Main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # Status label
        self.status_label = QLabel("Click 'Start Recording' to begin")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Audio level meter
        self.level_meter = QProgressBar()
        self.level_meter.setRange(0, 100)
        self.level_meter.setValue(0)
        layout.addWidget(self.level_meter)
        
        # Auto-stop timer display
        self.timer_label = QLabel("Max recording time: 30s")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)
        
        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        # Server URL input
        self.server_label = QLabel(f"Server URL: {self.server_url}")
        layout.addWidget(self.server_label)
        
        # Response display
        self.response_label = QLabel("Response:")
        layout.addWidget(self.response_label)
        
        self.response_text = QTextEdit()
        self.response_text.setReadOnly(True)
        layout.addWidget(self.response_text)
        
        # Initialize timer for auto-stopping after 30 seconds
        self.recording_timer = QTimer()
        self.recording_timer.setInterval(30000)  # 30 seconds
        self.recording_timer.setSingleShot(True)
        self.recording_timer.timeout.connect(self.auto_stop_recording)
        
        # Initialize timer for updating the countdown
        self.countdown_timer = QTimer()
        self.countdown_timer.setInterval(1000)  # 1 second
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_value = 30
    
    def toggle_recording(self):
        """Start or stop recording based on current state"""
        if self.recorder is None or not self.recorder.is_recording:
            # Start recording
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Starting microphone...")
            self.response_text.clear()
            
            self.recorder = AudioRecorder()
            self.recorder.update_status.connect(self.update_status)
            self.recorder.update_level.connect(self.level_meter.setValue)
            self.recorder.start()
            
            # Start timers for auto-stop
            self.recording_timer.start()
            self.countdown_value = 30
            self.countdown_timer.start()
        else:
            # Stop recording
            self.stop_recording()
    
    def stop_recording(self):
        """Stop the current recording and process the audio"""
        self.record_button.setText("Start Recording")
        self.recording_timer.stop()
        self.countdown_timer.stop()
        self.timer_label.setText("Max recording time: 30s")
        
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
            # Wait a bit for recorder to finish saving
            QThread.msleep(500)
            # Send the audio file to the API
            threading.Thread(target=self.send_audio_file, 
                           args=(self.recorder.audio_file_path,)).start()
    
    def auto_stop_recording(self):
        """Automatically stop recording after timeout"""
        self.status_label.setText("Maximum recording time reached")
        self.stop_recording()
    
    def update_countdown(self):
        """Update the countdown timer display"""
        self.countdown_value -= 1
        self.timer_label.setText(f"Time remaining: {self.countdown_value}s")
    
    def update_status(self, message):
        """Update the status label with a message"""
        self.status_label.setText(message)
    
    def send_audio_file(self, file_path):
        """Send audio file to the API and display the response"""
        try:
            if not file_path or not os.path.exists(file_path):
                self.update_status("Error: Audio file not found")
                return
                
            self.update_status(f"Sending audio to server...")
            
            with open(file_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                response = requests.post(self.server_url, files=files, timeout=30)
            
            # Display response in the text area
            response_data = response.json()
            
            if response.status_code == 200:
                self.update_status("Response received")
                
                # Format the response for display
                formatted_response = f"Query: {response_data.get('text_query', 'Unknown')}\n\n"
                formatted_response += f"Response:\n{response_data.get('response_text', 'No response')}"
                
                self.response_text.setText(formatted_response)
            else:
                error_message = f"Error: {response_data.get('error', 'Unknown error')}"
                self.update_status(error_message)
                self.response_text.setText(error_message)
                
            # Clean up the temporary file
            try:
                os.unlink(file_path)
            except:
                pass
                
        except requests.exceptions.ConnectionError:
            self.update_status("Error: Cannot connect to server. Is the API running?")
            self.response_text.setText("Connection Error: Make sure the API server is running at " + self.server_url)
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.response_text.setText(f"An error occurred: {str(e)}")

def send_audio_file(file_path):
    """
    Sends an audio file to the voice API endpoint
    
    Args:
        file_path: Path to the audio file to send
    """
    url = "http://localhost:5000/api/voice"
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found!")
        return
    
    print(f"Sending audio file {file_path} to server...")
    
    try:
        with open(file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            response = requests.post(url, files=files, timeout=30)
        
        print("Response status:", response.status_code)
        print("Response content:")
        print(response.json())
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to server. Is the API running at", url, "?")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Check if we're using the GUI or command-line mode
    if len(sys.argv) == 1:
        # Run in GUI mode
        app = QApplication(sys.argv)
        window = VoiceQueryApp()
        window.show()
        sys.exit(app.exec_())
    else:
        # Run in command-line mode
        parser = argparse.ArgumentParser(description='Test the voice API by sending an audio file')
        parser.add_argument('file_path', type=str, help='Path to the audio file (.wav format recommended)')
        
        args = parser.parse_args()
        send_audio_file(args.file_path)