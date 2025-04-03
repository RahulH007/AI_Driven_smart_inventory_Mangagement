import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import groq
from firebase_admin import credentials, messaging
import json
from dataclasses import dataclass
from config import GORQ_API_KEY, FIREBASE_CREDENTIALS

# Configure logging
logging.basicConfig(
    filename='logs/llm_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class LLMMetrics:
    response_time: float
    token_count: int
    error_rate: float
    success_rate: float
    cost: float
    timestamp: datetime

class LLMMonitor:
    def __init__(self, api_key: str, notification_topic: str = "llm_alerts"):
        self.api_key = api_key
        self.notification_topic = notification_topic
        self.metrics_history: List[LLMMetrics] = []
        self.thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.1,     # 10%
            "cost": 0.50,          # dollars per request
        }
        
        # Initialize Firebase
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        # firebase_admin.initialize_app(cred)

    def record_metrics(self, metrics: LLMMetrics):
        """Record metrics and check for anomalies"""
        self.metrics_history.append(metrics)
        self._check_anomalies(metrics)

    def _check_anomalies(self, metrics: LLMMetrics):
        """Check if metrics exceed thresholds and send notifications"""
        alerts = []

        if metrics.response_time > self.thresholds["response_time"]:
            alerts.append(f"High response time: {metrics.response_time:.2f}s")

        if metrics.error_rate > self.thresholds["error_rate"]:
            alerts.append(f"High error rate: {metrics.error_rate:.2%}")

        if metrics.cost > self.thresholds["cost"]:
            alerts.append(f"High cost: ${metrics.cost:.2f}")

        if alerts:
            self._send_notification(alerts)

    def _send_notification(self, alerts: List[str]):
        """Send notification through Firebase"""
        message = {
            "topic": self.notification_topic,
            "notification": {
                "title": "LLM Performance Alert",
                "body": "\n".join(alerts)
            },
            "data": {
                "timestamp": datetime.now().isoformat(),
                "alert_count": str(len(alerts))
            }
        }
        
        try:
            messaging.send(message)
            logging.info(f"Notification sent: {alerts}")
        except Exception as e:
            logging.error(f"Failed to send notification: {str(e)}")

    def get_performance_report(self) -> Dict:
        """Generate a performance report"""
        if not self.metrics_history:
            return {"error": "No metrics recorded"}

        recent_metrics = self.metrics_history[-100:]  # Last 100 metrics
        
        return {
            "average_response_time": sum(m.response_time for m in recent_metrics) / len(recent_metrics),
            "average_token_count": sum(m.token_count for m in recent_metrics) / len(recent_metrics),
            "average_error_rate": sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            "average_cost": sum(m.cost for m in recent_metrics) / len(recent_metrics),
            "total_requests": len(recent_metrics),
            "timestamp": datetime.now().isoformat()
        }

    def monitor_request(self, prompt: str, max_tokens: int = 1000) -> Dict:
        """Monitor a single LLM request"""
        start_time = time.time()
        try:
            # Make the actual LLM request
            response = groq.query(
                prompt,
                max_tokens=max_tokens,
                api_key=self.api_key
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            metrics = LLMMetrics(
                response_time=response_time,
                token_count=len(response.get("text", "").split()),
                error_rate=0.0,
                success_rate=1.0,
                cost=0.0,  # Calculate based on your pricing model
                timestamp=datetime.now()
            )
            
            self.record_metrics(metrics)
            return {"success": True, "response": response, "metrics": metrics}
            
        except Exception as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            metrics = LLMMetrics(
                response_time=response_time,
                token_count=0,
                error_rate=1.0,
                success_rate=0.0,
                cost=0.0,
                timestamp=datetime.now()
            )
            
            self.record_metrics(metrics)
            return {"success": False, "error": str(e), "metrics": metrics}

def main():
    """Main function to demonstrate usage"""
    monitor = LLMMonitor(api_key=GORQ_API_KEY)
    
    # Example monitoring loop
    while True:
        try:
            # Monitor a test request
            result = monitor.monitor_request("What is the weather today?")
            
            # Generate and log performance report
            report = monitor.get_performance_report()
            logging.info(f"Performance Report: {json.dumps(report, indent=2)}")
            
            # Wait for 5 minutes before next check
            time.sleep(300)
            
        except Exception as e:
            logging.error(f"Error in monitoring loop: {str(e)}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    main()