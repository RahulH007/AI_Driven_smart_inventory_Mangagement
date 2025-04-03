import os
from typing import Dict, Any, Optional
import tempfile
import io
import base64
import torch
import soundfile as sf
import numpy as np
from transformers import pipeline

class VoiceProcessingService:
    def __init__(self, chat_service):
        """
        Initialize the voice processing service
        
        Args:
            chat_service: The existing chat service for processing text queries
        """
        self.chat_service = chat_service
        self.whisper_model = None  # Placeholder for the Whisper model
        
        # Supported languages for TTS
        self.supported_languages = {
            'en': {'name': 'English', 'code': 'en'},
            'hi': {'name': 'Hindi', 'code': 'hi'},
            'kn': {'name': 'Kannada', 'code': 'kn'}
        }

    def _load_whisper_model(self):
        """Load the Whisper model on first use to save memory"""
        if self.whisper_model is None:
            print("Loading Whisper model...")
            self.whisper_model = pipeline("automatic-speech-recognition", model="openai/whisper-small")
            print("Whisper model loaded")

    async def process_voice_query(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process a voice query from audio data
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Dict containing the response and audio response
        """
        try:
            # Save audio data to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert speech to text
            text_query = await self.speech_to_text(temp_audio_path)
            
            if not text_query:
                return {
                    "status": "error",
                    "error": "Could not understand audio. Please try again."
                }
            
            # Process the query directly using the chat service
            response = await self.chat_service.process_query(text_query)
            
            # Get response text
            response_text = response.get("response", "")
            
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except:
                pass  # Ignore cleanup errors
            
            return {
                "status": "success",
                "text_query": text_query,
                "response_text": response_text,
                "context": response.get("context", {})
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error processing voice query: {str(e)}"
            }

    async def speech_to_text(self, audio_file_path: str) -> str:
        """
        Convert speech to text using Whisper
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        # Load Whisper model if not already loaded
        self._load_whisper_model()
        
        try:
            # Perform speech recognition
            result = self.whisper_model(audio_file_path)
            text = result["text"].strip()  # Get the transcribed text
            
            return text
        except Exception as e:
            print(f"Speech recognition error: {str(e)}")
            return ""

    def detect_language(self, text: str) -> str:
        """
        Detect language of input text
        
        Args:
            text: Input text
            
        Returns:
            Language code (default: 'en')
        """
        try:
            from langdetect import detect
            lang = detect(text)
            return lang if lang in self.supported_languages else 'en'
        except:
            return 'en'  # Default to English on error