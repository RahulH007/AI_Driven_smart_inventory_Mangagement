import time
import threading
import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("inventory_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InventoryAgent")

class InventoryAgent:
    """
    AI Agent that monitors inventory and generates notifications
    """
    def __init__(self, chat_service):
        self.chat_service = chat_service
        self.is_running = False
        self.agent_thread = None
        self.check_interval = 3600  # Default: check every hour
        self.notification_storage_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'notifications.json')
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.notification_storage_path), exist_ok=True)
        
        # Load existing notifications if file exists
        self.notifications = []
        self.load_notifications()
        
        logger.info("Inventory Agent initialized")
    
    def start(self, check_interval=None):
        """Start the agent in the background"""
        if check_interval:
            self.check_interval = check_interval
            
        if self.is_running:
            logger.warning("Agent is already running")
            return
            
        self.is_running = True
        self.agent_thread = threading.Thread(target=self._monitoring_loop)
        self.agent_thread.daemon = True
        self.agent_thread.start()
        logger.info(f"Inventory monitoring started with interval of {self.check_interval} seconds")
        
        # Run an immediate check
        threading.Thread(target=self._run_check).start()
    
    def stop(self):
        """Stop the agent"""
        if not self.is_running:
            logger.warning("Agent is not running")
            return
            
        self.is_running = False
        if self.agent_thread:
            self.agent_thread.join(timeout=1.0)
        logger.info("Inventory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs checks periodically"""
        while self.is_running:
            try:
                self._run_check()
                
                # Sleep for the check interval
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Sleep for 1 minute on error
    
    def _run_check(self):
        """Run a single inventory check"""
        try:
            logger.info("Running inventory check")
            
            # Create a new event loop for the async call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the notification generation
            notifications = loop.run_until_complete(self.chat_service.generate_notifications())
            
            # Close the loop
            loop.close()
            
            if notifications.get("status") == "success":
                self._process_new_notifications(notifications.get("notifications", []))
                logger.info(f"Check completed: {len(notifications.get('notifications', []))} notifications generated")
            else:
                logger.error(f"Error generating notifications: {notifications.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error running inventory check: {str(e)}")
    
    def _process_new_notifications(self, new_notifications):
        """Process new notifications and save them"""
        now = datetime.now()
        today_iso = now.date().isoformat()
        
        # Add any new notifications that don't already exist
        added = 0
        for notification in new_notifications:
            # Generate a simple notification ID
            notification_id = f"{notification['type']}_{notification.get('product_id', 'general')}_{today_iso}"
            
            # Check if this notification already exists for today
            exists = False
            for existing in self.notifications:
                if existing.get('id') == notification_id and today_iso in existing.get('timestamp', ''):
                    exists = True
                    break
            
            if not exists:
                # Add ID and make sure timestamp is present
                notification['id'] = notification_id
                if 'timestamp' not in notification:
                    notification['timestamp'] = now.isoformat()
                
                # Add to the beginning of the list to show newest first
                self.notifications.insert(0, notification)
                added += 1
        
        # Limit to 50 most recent notifications
        self.notifications = self.notifications[:50]
        
        if added > 0:
            logger.info(f"Added {added} new notifications")
            self.save_notifications()
    
    def get_notifications(self, limit=20):
        """Get the most recent notifications"""
        return {
            "notifications": self.notifications[:limit],
            "status": "success"
        }
    
    def save_notifications(self):
        """Save notifications to disk"""
        try:
            with open(self.notification_storage_path, 'w') as f:
                json.dump(self.notifications, f)
        except Exception as e:
            logger.error(f"Error saving notifications: {str(e)}")
    
    def load_notifications(self):
        """Load notifications from disk"""
        try:
            if os.path.exists(self.notification_storage_path):
                with open(self.notification_storage_path, 'r') as f:
                    self.notifications = json.load(f)
                logger.info(f"Loaded {len(self.notifications)} notifications from storage")
        except Exception as e:
            logger.error(f"Error loading notifications: {str(e)}")
            self.notifications = []
```