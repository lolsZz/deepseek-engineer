"""Monitoring system for telemetry and logging."""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
from queue import Queue
import traceback
import psutil
import platform
from contextlib import contextmanager

@dataclass
class Metric:
    """Represents a single metric measurement."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]

@dataclass
class Event:
    """Represents a system event."""
    name: str
    timestamp: datetime
    data: Dict[str, Any]
    level: str

class MetricsAggregator:
    """Aggregates and processes metrics."""
    
    def __init__(self):
        """Initialize metrics storage."""
        self.metrics: Dict[str, List[Metric]] = {}
        self._lock = threading.Lock()
    
    def add_metric(self, metric: Metric):
        """Add a new metric measurement."""
        with self._lock:
            if metric.name not in self.metrics:
                self.metrics[metric.name] = []
            self.metrics[metric.name].append(metric)
    
    def get_metrics(self, name: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Metric]:
        """Get metrics for a given name within time range."""
        with self._lock:
            if name not in self.metrics:
                return []
            
            metrics = self.metrics[name]
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]
            return metrics
    
    def clear_old_metrics(self, before: datetime):
        """Remove metrics older than specified time."""
        with self._lock:
            for name in self.metrics:
                self.metrics[name] = [
                    m for m in self.metrics[name]
                    if m.timestamp > before
                ]

class EventProcessor:
    """Processes and stores system events."""
    
    def __init__(self, max_events: int = 1000):
        """Initialize event storage."""
        self.max_events = max_events
        self.events: List[Event] = []
        self._lock = threading.Lock()
    
    def add_event(self, event: Event):
        """Add a new event."""
        with self._lock:
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events.pop(0)
    
    def get_events(self, 
                  level: Optional[str] = None,
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None) -> List[Event]:
        """Get events filtered by level and time range."""
        with self._lock:
            events = self.events
            if level:
                events = [e for e in events if e.level == level]
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]
            return events

class PerformanceMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self):
        """Initialize performance monitoring."""
        self.process = psutil.Process()
    
    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system performance metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "process_cpu_percent": self.process.cpu_percent(),
            "process_memory_percent": self.process.memory_percent()
        }
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get detailed process information."""
        return {
            "pid": self.process.pid,
            "status": self.process.status(),
            "create_time": datetime.fromtimestamp(self.process.create_time()),
            "num_threads": self.process.num_threads(),
            "num_fds": self.process.num_fds() if platform.system() != "Windows" else None,
            "cpu_times": self.process.cpu_times()._asdict(),
            "memory_info": self.process.memory_info()._asdict()
        }

class MonitoringSystem:
    """Central monitoring system for telemetry and logging."""
    
    def __init__(self, log_path: Optional[Path] = None):
        """Initialize monitoring system."""
        self.metrics = MetricsAggregator()
        self.events = EventProcessor()
        self.performance = PerformanceMonitor()
        self.log_path = log_path
        
        # Set up logging
        self._setup_logging()
        
        # Background worker for periodic tasks
        self._worker_queue: Queue = Queue()
        self._worker_thread = threading.Thread(target=self._background_worker, daemon=True)
        self._worker_thread.start()
    
    def _setup_logging(self):
        """Configure logging system."""
        self.logger = logging.getLogger("deepseek_engineer")
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if path provided
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _background_worker(self):
        """Background worker for periodic tasks."""
        while True:
            try:
                # Collect performance metrics
                metrics = self.performance.get_system_metrics()
                for name, value in metrics.items():
                    self.record_metric(name, value)
                
                # Clean up old metrics (keep last 24 hours)
                self.metrics.clear_old_metrics(
                    datetime.now() - timedelta(hours=24)
                )
                
                time.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.record_error("Background worker error", error=e)
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric measurement."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels or {}
        )
        self.metrics.add_metric(metric)
    
    def record_event(self, name: str, data: Dict[str, Any], level: str = "INFO"):
        """Record a system event."""
        event = Event(
            name=name,
            timestamp=datetime.now(),
            data=data,
            level=level
        )
        self.events.add_event(event)
        
        # Also log the event
        log_message = f"{name}: {json.dumps(data)}"
        if level == "ERROR":
            self.logger.error(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def record_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Record an error event with stack trace."""
        data = {
            "message": message,
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None,
            "stack_trace": traceback.format_exc() if error else None,
            **kwargs
        }
        self.record_event("error", data, level="ERROR")
    
    @contextmanager
    def measure_time(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager to measure operation execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_metric(
                f"{operation_name}_duration_seconds",
                duration,
                labels
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": self.performance.get_system_metrics(),
            "process_info": self.performance.get_process_info(),
            "recent_errors": [
                asdict(e) for e in self.events.get_events(
                    level="ERROR",
                    start_time=datetime.now() - timedelta(hours=1)
                )
            ]
        }
    
    def export_metrics(self, path: Path):
        """Export all metrics to a file."""
        data = {
            name: [asdict(m) for m in metrics]
            for name, metrics in self.metrics.metrics.items()
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def export_events(self, path: Path):
        """Export all events to a file."""
        data = [asdict(e) for e in self.events.events]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)