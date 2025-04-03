import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.chat_service import InventoryChatService
from backend.voice_service import VoiceProcessingService

async def process_voice_input(audio_file_path):
    """
    Process a voice input file and get a response from the LLM
    
    Args:
        audio_file_path: Path to the audio file
    """
    # Initialize the chat service first
    chat_service = InventoryChatService()
    
    # Initialize the voice service with the chat service
    voice_service = VoiceProcessingService(chat_service)
    
    # Read the audio file
    with open(audio_file_path, 'rb') as f:
        audio_data = f.read()
    
    # Process the voice query
    result = await voice_service.process_voice_query(audio_data)
    
    # Display the results
    if result['status'] == 'success':
        print(f"Recognized text: {result['text_query']}")
        print("\nResponse:")
        print(result['response_text'])
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")

def print_example_trend_queries():
    """Print example inventory trend queries to try with voice"""
    simple_examples = [
        "How many Dove Shampoo bottles are in stock?",
        "What's the price of Tata Tea?",
        "Do we have Maggi Noodles?"
    ]
    
    trend_examples = [
        "Which products should I restock soon?",
        "Which products are not selling well?",
        "What are our best selling items?",
        "Is Dove Shampoo selling faster than Colgate toothpaste?",
        "How many Tata Tea packages should I order?"
    ]
    
    print("\nSimple inventory questions (without trend analysis):")
    for example in simple_examples:
        print(f"- \"{example}\"")
        
    print("\nTrend analysis questions (with detailed recommendations):")
    for example in trend_examples:
        print(f"- \"{example}\"")
    
    print("\nNOTE: Be sure to include words like 'trend', 'restock', or 'selling' when")
    print("      you want detailed sales analysis in the response.")
    print()

def simple_voice_query(audio_file_path):
    """
    Simple function to process voice from a file
    """
    asyncio.run(process_voice_input(audio_file_path))

# Example usage
if __name__ == "__main__":
    print_example_trend_queries()
    file_path = input("Enter path to audio file: ")
    if os.path.exists(file_path):
        simple_voice_query(file_path)
    else:
        print(f"File not found: {file_path}")