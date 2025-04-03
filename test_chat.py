import requests
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def chat_with_database(query):
    url = "http://localhost:5000/api/chat"
    payload = {
        "query": query
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def print_example_questions():
    """Print some example questions for inventory trend analysis"""
    simple_examples = [
        "How many Dove Shampoo bottles do we have in stock?",
        "What's the price of Tata Tea Premium?",
        "List all products with less than 20 items in stock",
        "When did we add Amul Butter to our inventory?",
        "What products do we sell?"
    ]
    
    trend_examples = [
        "Based on sales trends, which products should I restock soon?",
        "Which products are moving slowly and shouldn't be restocked?",
        "What are the best selling products in our inventory?",
        "Show me the sales velocity for our top products",
        "Which product has the fastest turnover rate?",
        "What quantity of Dove Shampoo should I order next time?",
        "Is Maggi Noodles selling well compared to other products?",
        "Based on current sales, what's my projected inventory in 2 weeks?"
    ]
    
    print("\nSimple inventory questions (without trend analysis):")
    for i, example in enumerate(simple_examples, 1):
        print(f"{i}. {example}")
    
    print("\nTrend analysis questions (with detailed recommendations):")
    for i, example in enumerate(trend_examples, 1):
        print(f"{i}. {example}")
    print()
    print("NOTE: Trend analysis will ONLY be included for queries that explicitly ask about")
    print("trends, recommendations, sales performance, or restocking decisions.")
    print()

if __name__ == "__main__":
    print_example_questions()
    
    while True:
        user_query = input("\nAsk about your inventory (type 'exit' to quit, 'examples' to see sample questions): ")
        if user_query.lower() == 'exit':
            break
        elif user_query.lower() == 'examples':
            print_example_questions()
            continue
            
        print("\nProcessing your query...")
        result = chat_with_database(user_query)
        
        if result.get("status") == "success":
            print("\nResponse:")
            print(result.get("response"))
        else:
            print("\nError:", result.get("error") or "Unknown error occurred")