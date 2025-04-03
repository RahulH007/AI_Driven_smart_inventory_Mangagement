import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    credentials_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    
    if not credentials_path:
        raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is not set")
    
    if not os.path.exists(credentials_path):
        raise ValueError(f"Firebase credentials file not found at: {credentials_path}")
    
    print(f"Loading Firebase credentials from: {credentials_path}")
    cred = credentials.Certificate(credentials_path)
    firebase_admin.initialize_app(cred)
    return firestore.client()

# Initialize Firestore client
db = initialize_firebase()