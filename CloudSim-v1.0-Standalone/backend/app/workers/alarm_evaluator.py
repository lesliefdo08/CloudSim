"""
Alarm Evaluator Worker
Periodically evaluates alarms and triggers actions
"""
import threading
import time
from datetime import datetime

from app.core.database import SessionLocal
from app.services.cloudwatch_alarms_service import CloudWatchAlarmsService


class AlarmEvaluator:
    """Background worker for alarm evaluation."""
    
    def __init__(self, evaluation_interval: int = 60):
        """
        Initialize alarm evaluator.
        
        Args:
            evaluation_interval: Seconds between evaluations (default: 60)
        """
        self.evaluation_interval = evaluation_interval
        self.alarms_service = CloudWatchAlarmsService()
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the alarm evaluator."""
        if self.running:
            print("Alarm evaluator already running")
            return
        
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"Alarm evaluator started (interval: {self.evaluation_interval}s)")
    
    def stop(self):
        """Stop the alarm evaluator."""
        if not self.running:
            return
        
        print("Stopping alarm evaluator...")
        self.running = False
        self._stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("Alarm evaluator stopped")
    
    def _run(self):
        """Main evaluation loop."""
        while self.running and not self._stop_event.is_set():
            try:
                self._evaluate_alarms()
            except Exception as e:
                print(f"Error in alarm evaluation: {str(e)}")
            
            # Wait for next interval
            self._stop_event.wait(self.evaluation_interval)
    
    def _evaluate_alarms(self):
        """Evaluate all alarms."""
        db = SessionLocal()
        try:
            start_time = datetime.utcnow()
            results = self.alarms_service.evaluate_all_alarms(db)
            
            # Log state changes
            changes = [r for r in results if r["old_state"] != r["new_state"]]
            if changes:
                print(f"Alarm evaluation completed: {len(changes)} state changes")
                for change in changes:
                    alarm = change["alarm"]
                    print(f"  {alarm.alarm_name}: {change['old_state']} -> {change['new_state']}")
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            print(f"Evaluated {len(results)} alarms in {elapsed:.2f}s")
        
        except Exception as e:
            print(f"Error evaluating alarms: {str(e)}")
        finally:
            db.close()


# Global evaluator instance
_alarm_evaluator = None


def get_alarm_evaluator() -> AlarmEvaluator:
    """Get the global alarm evaluator instance."""
    global _alarm_evaluator
    if _alarm_evaluator is None:
        _alarm_evaluator = AlarmEvaluator()
    return _alarm_evaluator


def start_alarm_evaluator():
    """Start the global alarm evaluator."""
    evaluator = get_alarm_evaluator()
    evaluator.start()


def stop_alarm_evaluator():
    """Stop the global alarm evaluator."""
    evaluator = get_alarm_evaluator()
    evaluator.stop()
