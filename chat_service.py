import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
import google.generativeai as genai
from firebase_admin import firestore
from backend.firebase_config import db

class ChatService:
    def __init__(self):
        # Initialize any necessary variables or connections
        pass

    def process_query(self, query: str) -> dict:
        # Logic to process the query and return a response
        response = {
            "response": "This is a placeholder response for the query: " + query
        }
        return response

class InventoryChatService:
    def __init__(self):
        """Initialize the chat service with Firebase and Google Gemini"""
        # Configure the Gemini API
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        
        # Use Gemini 1.5 Flash model
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.db = db
        
        # Define system prompt with enhanced analysis capabilities
        self.system_prompt = """
        You are an AI assistant for a small grocery store inventory management system. You have access to the Firebase database
        with the following collections:
        
        - products: Contains product information (barcode_id, name, price, quantity, entry_date)
        - sales: Contains sales information (product_id, quantity_sold, selling_date, total_price)
        
        IMPORTANT CAPABILITIES:
        1. Provide detailed inventory analysis based on sales trends
        2. Recommend products to restock based on:
           - High sales volume (popular products)
           - Sales velocity (how quickly products sell after entry)
           - Current inventory levels
        3. Identify slow-moving products that should not be restocked
        4. Calculate optimal reorder quantities based on historical sales data
        5. Identify seasonal trends if they appear in the data
        
        Always include specific data points to support your recommendations, such as:
        - Exact sales numbers
        - Days between entry and sale
        - Current stock levels
        - Profit margins when available
        
        Format your responses in a clear, structured manner with sections for:
        - Analysis summary
        - Product-specific recommendations
        - Data-backed justifications
        """

    async def get_collection_data(self, collection_name: str) -> List[Dict]:
        """
        Get all documents from a collection
        """
        docs = self.db.collection(collection_name).stream()
        return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

    async def calculate_sales_velocity(self, products: List[Dict], sales: List[Dict]) -> Dict[str, Any]:
        """
        Calculate sales velocity for products (how quickly they sell after being stocked)
        """
        velocity_data = {}
        
        # Create a lookup dictionary for products by barcode
        product_dict = {p['barcode_id']: p for p in products if 'barcode_id' in p}
        
        # Group sales by product_id
        sales_by_product = {}
        for sale in sales:
            if 'product_id' not in sale:
                continue
                
            product_id = sale['product_id']
            if product_id not in sales_by_product:
                sales_by_product[product_id] = []
            sales_by_product[product_id].append(sale)
        
        # Calculate velocity for each product
        for product_id, product_sales in sales_by_product.items():
            if product_id not in product_dict:
                continue
                
            product = product_dict[product_id]
            
            # Skip if no entry date
            if 'entry_date' not in product:
                continue
                
            entry_date = product['entry_date']
            total_sold = sum(sale.get('quantity_sold', 0) for sale in product_sales)
            
            # Calculate average days to sell
            if total_sold > 0:
                days_to_sell = []
                for sale in product_sales:
                    if 'selling_date' in sale:
                        selling_date = sale['selling_date']
                        # Calculate days between entry and sale
                        if hasattr(selling_date, 'timestamp') and hasattr(entry_date, 'timestamp'):
                            days_diff = (selling_date - entry_date).total_seconds() / 86400  # Convert to days
                            days_to_sell.append(days_diff)
                
                avg_days_to_sell = sum(days_to_sell) / len(days_to_sell) if days_to_sell else None
                
                # Store velocity data
                velocity_data[product_id] = {
                    'name': product.get('name', 'Unknown Product'),
                    'total_sold': total_sold,
                    'avg_days_to_sell': avg_days_to_sell,
                    'current_stock': product.get('quantity', 0),
                    'price': product.get('price', 0),
                    'entry_date': product.get('entry_date')
                }
        
        return velocity_data

    async def get_restocking_recommendations(self) -> Dict[str, Any]:
        """
        Generate restocking recommendations based on sales trends
        """
        products = await self.get_collection_data('products')
        sales = await self.get_collection_data('sales')
        
        # Calculate sales velocity
        velocity_data = await self.calculate_sales_velocity(products, sales)
        
        # Sort products by sales velocity
        fast_moving = []
        slow_moving = []
        
        for product_id, data in velocity_data.items():
            if data['avg_days_to_sell'] is not None:
                if data['avg_days_to_sell'] < 7 and data['current_stock'] < 20:  # Fast-moving threshold
                    fast_moving.append({
                        'product_id': product_id,
                        'name': data['name'],
                        'days_to_sell': data['avg_days_to_sell'],
                        'current_stock': data['current_stock'],
                        'recommended_order': int(data['total_sold'] * 1.5)  # Simple ordering logic
                    })
                elif data['avg_days_to_sell'] > 20 and data['current_stock'] > 10:  # Slow-moving threshold
                    slow_moving.append({
                        'product_id': product_id,
                        'name': data['name'],
                        'days_to_sell': data['avg_days_to_sell'],
                        'current_stock': data['current_stock']
                    })
        
        return {
            'fast_moving': fast_moving,
            'slow_moving': slow_moving,
            'velocity_data': velocity_data
        }

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query about inventory using Google's Gemini 1.5 Flash and Firestore data
        """
        try:
            # Fetch relevant data from Firestore
            products = await self.get_collection_data('products')
            sales = await self.get_collection_data('sales')
            
            # Define specific trend analysis phrases that require advanced analysis
            trend_analysis_phrases = [
                "trend", "recommend", "restock", "restocking", 
                "best sell", "fast sell", "slow sell", "popular", 
                "sales velocity", "turnover rate", "moving products",
                "should i order", "how many to order", "projected inventory"
            ]
            
            # Check if query explicitly asks for trend analysis
            is_trend_query = False
            user_query_lower = user_query.lower()
            
            for phrase in trend_analysis_phrases:
                if phrase in user_query_lower:
                    is_trend_query = True
                    break
                    
            # Only add trend analysis for explicit trend-related queries
            additional_context = {}
            if is_trend_query:
                recommendations = await self.get_restocking_recommendations()
                additional_context = {
                    'recommendations': recommendations
                }

            # Prepare context with database information
            context = {
                'products': products,
                'sales': sales,
                **additional_context
            }

            # Create chat completion with Gemini
            # Basic prompt for simple inventory queries
            if not is_trend_query:
                prompt = f"""
                You are an AI assistant for a small grocery store inventory management system. You have access to the Firebase database
                with the following collections:
                
                - products: Contains product information (barcode_id, name, price, quantity, entry_date)
                - sales: Contains sales information (product_id, quantity_sold, selling_date, total_price)
                
                Answer the user's questions about inventory, products, and sales in a clear, concise manner.
                DO NOT perform any trend analysis or make restocking recommendations unless explicitly requested.
                
                Here is the current database state:
                Products: {str(products)}
                Sales: {str(sales)}
                
                User question: {user_query}
                """
            # Enhanced prompt for trend analysis queries
            else:
                prompt = f"""
                {self.system_prompt}
                
                Here is the current database state:
                Products: {str(products)}
                Sales: {str(sales)}
                
                Sales Trend Analysis: {str(additional_context)}
                
                User question: {user_query}
                """
            
            response = self.model.generate_content(prompt)

            # Store the conversation in Firestore
            await self.store_conversation(user_query, response.text)

            return {
                "response": response.text,
                "status": "success",
                "context": context
            }

        except Exception as e:
            return {
                "response": f"Error processing query: {str(e)}",
                "status": "error"
            }

    async def store_conversation(self, query: str, response: str):
        """
        Store conversation history in Firestore
        """
        self.db.collection('chat_history').add({
            'query': query,
            'response': response,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

    async def get_inventory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current inventory status
        """
        try:
            products_ref = self.db.collection('products')
            sales_ref = self.db.collection('sales')
            
            # Get all products
            products = await self.get_collection_data('products')
            
            # Calculate summary statistics
            total_products = len(products)
            total_items = sum(p.get('quantity', 0) for p in products)
            average_price = sum(p.get('price', 0) for p in products) / total_products if total_products > 0 else 0
            
            # Get total sales
            total_sales = sum(s.get('quantity_sold', 0) for s in sales)
            
            summary = {
                "total_products": total_products,
                "total_items": total_items,
                "average_price": average_price,
                "total_sales": total_sales
            }

            return {
                "response": summary,
                "status": "success"
            }

        except Exception as e:
            return {
                "response": f"Error generating inventory summary: {str(e)}",
                "status": "error"
            }

    async def generate_notifications(self) -> Dict[str, Any]:
        """
        Generate notifications based on inventory status and sales trends
        """
        try:
            products = await self.get_collection_data('products')
            sales = await self.get_collection_data('sales')
            
            # Get restocking recommendations
            recommendations = await self.get_restocking_recommendations()
            
            notifications = []
            
            # Check for low stock items (less than 15 units)
            low_stock_items = [p for p in products if p.get('quantity', 0) < 15]
            for item in low_stock_items:
                notifications.append({
                    "type": "warning",
                    "message": f"Low stock alert: {item.get('name')} has only {item.get('quantity')} units left",
                    "timestamp": datetime.now().isoformat(),
                    "product_id": item.get('barcode_id')
                })
            
            # Add notifications for fast-moving items
            for item in recommendations.get('fast_moving', []):
                notifications.append({
                    "type": "info",
                    "message": f"{item.get('name')} is selling well (avg {item.get('days_to_sell', 0):.1f} days to sell). Consider ordering {item.get('recommended_order', 0)} more units.",
                    "timestamp": datetime.now().isoformat(),
                    "product_id": item.get('product_id')
                })
            
            # Add notifications for slow-moving items
            for item in recommendations.get('slow_moving', []):
                notifications.append({
                    "type": "alert",
                    "message": f"{item.get('name')} is moving slowly (avg {item.get('days_to_sell', 0):.1f} days to sell). Consider reducing stock.",
                    "timestamp": datetime.now().isoformat(),
                    "product_id": item.get('product_id')
                })
            
            # Sort by notification type (warnings first, then alerts, then info)
            def get_notification_priority(notification):
                if notification["type"] == "warning":
                    return 0
                elif notification["type"] == "alert":
                    return 1
                else:
                    return 2
                    
            notifications.sort(key=get_notification_priority)
            
            return {
                "notifications": notifications,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error generating notifications: {str(e)}"
            }