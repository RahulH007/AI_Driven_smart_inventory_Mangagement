import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import datetime
import random
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Initialize Firebase
credentials_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
if not credentials_path:
    raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is not set")

try:
    cred = credentials.Certificate(credentials_path)
    firebase_admin.initialize_app(cred)
except ValueError:
    # App already initialized
    pass

db = firestore.client()

# Sample products with barcode IDs
sample_products = [
    {
        "barcode_id": "8901030704994",
        "name": "Dove Shampoo 650ml",
        "price": 249.99,
        "quantity": 35,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=15)
    },
    {
        "barcode_id": "8901396313501",
        "name": "Surf Excel Detergent 1kg",
        "price": 199.99,
        "quantity": 42,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=12)
    },
    {
        "barcode_id": "8901314010559",
        "name": "Colgate Strong Teeth 200g",
        "price": 99.99,
        "quantity": 60,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=20)
    },
    {
        "barcode_id": "8901063010283",
        "name": "Tata Tea Premium 1kg",
        "price": 490.00,
        "quantity": 28,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=10)
    },
    {
        "barcode_id": "8901719110016",
        "name": "Aashirvaad Atta 5kg",
        "price": 275.00,
        "quantity": 15,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=8)
    },
    {
        "barcode_id": "8901058851298",
        "name": "Maggi Noodles 12 Pack",
        "price": 144.00,
        "quantity": 50,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=18)
    },
    {
        "barcode_id": "8901725121938",
        "name": "Parle-G Biscuits 800g",
        "price": 87.00,
        "quantity": 65,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=25)
    },
    {
        "barcode_id": "8901262150378",
        "name": "Amul Butter 500g",
        "price": 245.00,
        "quantity": 30,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=5)
    },
    {
        "barcode_id": "8901725121846",
        "name": "Fortune Sunflower Oil 5L",
        "price": 899.99,
        "quantity": 22,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=14)
    },
    {
        "barcode_id": "8901030707896",
        "name": "Lux Soap 125g (Pack of 3)",
        "price": 135.00,
        "quantity": 45,
        "entry_date": datetime.datetime.now() - datetime.timedelta(days=22)
    }
]

def generate_sales():
    """Generate sample sales data"""
    sales = []
    
    # For each product, create some sales records
    for product in sample_products:
        # Generate between 1 and 5 sales records per product
        for _ in range(random.randint(1, 5)):
            quantity_sold = random.randint(1, 10)
            selling_date = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))
            
            # Make sure selling date is after entry date
            if selling_date < product["entry_date"]:
                selling_date = product["entry_date"] + datetime.timedelta(days=random.randint(1, 5))
                
            sales.append({
                "product_id": product["barcode_id"],
                "quantity_sold": quantity_sold,
                "selling_date": selling_date,
                "total_price": quantity_sold * product["price"]
            })
    
    return sales

def populate_database():
    """Populate the database with sample data"""
    print("Starting database population...")
    
    # Clear existing data (optional)
    delete_collections = input("Do you want to delete existing collections before adding new data? (y/n): ")
    if delete_collections.lower() == 'y':
        collections = ['products', 'sales']
        for collection in collections:
            docs = db.collection(collection).stream()
            for doc in docs:
                doc.reference.delete()
                print(f"Deleted document {doc.id} from {collection}")
    
    # Add products
    for product in sample_products:
        # Use barcode_id as document ID
        doc_ref = db.collection('products').document(product["barcode_id"])
        doc_ref.set(product)
        print(f"Added product: {product['name']} with barcode {product['barcode_id']}")
    
    # Add sales
    sales = generate_sales()
    for sale in sales:
        doc_ref = db.collection('sales').document()
        doc_ref.set(sale)
        print(f"Added sale for product: {sale['product_id']}, quantity: {sale['quantity_sold']}")
    
    print("Database population completed!")

if __name__ == "__main__":
    populate_database()