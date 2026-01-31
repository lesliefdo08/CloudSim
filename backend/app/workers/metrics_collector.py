"""
Background worker for periodic CloudWatch metrics collection
"""
import time
import logging
from threading import Thread, Event
from typing import Optional

from app.core.database import SessionLocal
from app.services.cloudwatch_service import CloudWatchService


logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Background worker that periodically collects metrics from running instances.
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize metrics collector.
        
        Args:
            interval: Collection interval in seconds (default: 60)
        """
        self.interval = interval
        self.cloudwatch_service = CloudWatchService()
        self._stop_event = Event()
        self._thread: Optional[Thread] = None
    
    def start(self):
        """Start the metrics collection worker."""
        if self._thread and self._thread.is_alive():
            logger.warning("Metrics collector already running")
            return
        
        self._stop_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"Metrics collector started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop the metrics collection worker."""
        if not self._thread or not self._thread.is_alive():
            logger.warning("Metrics collector not running")
            return
        
        logger.info("Stopping metrics collector...")
        self._stop_event.set()
        self._thread.join(timeout=10)
        logger.info("Metrics collector stopped")
    
    def is_running(self) -> bool:
        """Check if the collector is running."""
        return self._thread is not None and self._thread.is_alive()
    
    def _run(self):
        """Main worker loop."""
        logger.info("Metrics collector worker started")
        
        while not self._stop_event.is_set():
            try:
                self._collect_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}", exc_info=True)
            
            # Wait for next interval (with early exit on stop)
            self._stop_event.wait(timeout=self.interval)
        
        logger.info("Metrics collector worker stopped")
    
    def _collect_metrics(self):
        """Collect metrics from all running instances."""
        db = SessionLocal()
        
        try:
            logger.debug("Collecting metrics from running instances...")
            
            results = self.cloudwatch_service.collect_all_instance_metrics(db)
            
            total_metrics = sum(len(metrics) for metrics in results.values())
            logger.info(f"Collected {total_metrics} metrics from {len(results)} instances")
            
        except Exception as e:
            logger.error(f"Error in metrics collection: {str(e)}", exc_info=True)
        finally:
            db.close()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(interval=60)
    
    return _metrics_collector


def start_metrics_collector():
    """Start the global metrics collector."""
    collector = get_metrics_collector()
    collector.start()


def stop_metrics_collector():
    """Stop the global metrics collector."""
    collector = get_metrics_collector()
    collector.stop()
