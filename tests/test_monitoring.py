"""Tests for the MonitoringSystem."""

import pytest
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import time
from queue import Queue
import psutil

from deepseek_engineer.core.monitoring import (
    MonitoringSystem,
    Metric,
    Event,
    MetricsAggregator,
    EventProcessor,
    PerformanceMonitor
)

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file."""
    return tmp_path / "test.log"

@pytest.fixture
def monitoring_system(temp_log_file):
    """Create a MonitoringSystem instance with test configuration."""
    return MonitoringSystem(log_path=temp_log_file)

def test_metric_recording(monitoring_system):
    """Test recording and retrieving metrics."""
    # Record some test metrics
    monitoring_system.record_metric("test_metric", 42.0, {"label": "test"})
    monitoring_system.record_metric("test_metric", 43.0, {"label": "test"})
    
    # Get recorded metrics
    metrics = monitoring_system.metrics.get_metrics("test_metric")
    assert len(metrics) == 2
    assert metrics[0].value == 42.0
    assert metrics[1].value == 43.0
    assert all(m.labels["label"] == "test" for m in metrics)

def test_event_recording(monitoring_system):
    """Test recording and retrieving events."""
    # Record test events
    monitoring_system.record_event("test_event", {"key": "value"}, "INFO")
    monitoring_system.record_event("error_event", {"error": "test"}, "ERROR")
    
    # Get all events
    events = monitoring_system.events.get_events()
    assert len(events) == 2
    
    # Get error events
    error_events = monitoring_system.events.get_events(level="ERROR")
    assert len(error_events) == 1
    assert error_events[0].name == "error_event"

def test_error_recording(monitoring_system):
    """Test error recording with stack traces."""
    try:
        raise ValueError("Test error")
    except Exception as e:
        monitoring_system.record_error("Test error occurred", e)
    
    # Get error events
    errors = monitoring_system.events.get_events(level="ERROR")
    assert len(errors) == 1
    assert "ValueError" in errors[0].data["error_type"]
    assert "Test error" in errors[0].data["error_message"]
    assert "stack_trace" in errors[0].data

def test_metrics_aggregator():
    """Test MetricsAggregator functionality."""
    aggregator = MetricsAggregator()
    
    # Add metrics
    metric1 = Metric("test", 1.0, datetime.now(), {})
    metric2 = Metric("test", 2.0, datetime.now(), {})
    aggregator.add_metric(metric1)
    aggregator.add_metric(metric2)
    
    # Test retrieval
    metrics = aggregator.get_metrics("test")
    assert len(metrics) == 2
    
    # Test time filtering
    future = datetime.now() + timedelta(hours=1)
    filtered = aggregator.get_metrics("test", end_time=future)
    assert len(filtered) == 2
    
    past = datetime.now() - timedelta(hours=1)
    filtered = aggregator.get_metrics("test", start_time=past)
    assert len(filtered) == 2
    
    # Test cleanup
    aggregator.clear_old_metrics(datetime.now() + timedelta(minutes=1))
    assert len(aggregator.get_metrics("test")) == 0

def test_event_processor():
    """Test EventProcessor functionality."""
    processor = EventProcessor(max_events=2)
    
    # Add events
    event1 = Event("test1", datetime.now(), {}, "INFO")
    event2 = Event("test2", datetime.now(), {}, "ERROR")
    event3 = Event("test3", datetime.now(), {}, "INFO")
    
    processor.add_event(event1)
    processor.add_event(event2)
    processor.add_event(event3)
    
    # Test max events limit
    events = processor.get_events()
    assert len(events) == 2
    assert events[0].name == "test2"  # Should have dropped test1
    assert events[1].name == "test3"
    
    # Test filtering
    error_events = processor.get_events(level="ERROR")
    assert len(error_events) == 1
    assert error_events[0].name == "test2"

@patch('psutil.Process')
@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
def test_performance_monitor(mock_disk, mock_memory, mock_cpu, mock_process):
    """Test PerformanceMonitor functionality."""
    # Setup mocks
    mock_cpu.return_value = 50.0
    mock_memory.return_value.percent = 60.0
    mock_disk.return_value.percent = 70.0
    mock_process.return_value.cpu_percent.return_value = 30.0
    mock_process.return_value.memory_percent.return_value = 40.0
    
    monitor = PerformanceMonitor()
    metrics = monitor.get_system_metrics()
    
    assert metrics["cpu_percent"] == 50.0
    assert metrics["memory_percent"] == 60.0
    assert metrics["disk_usage_percent"] == 70.0
    assert metrics["process_cpu_percent"] == 30.0
    assert metrics["process_memory_percent"] == 40.0

def test_time_measurement(monitoring_system):
    """Test operation time measurement."""
    with monitoring_system.measure_time("test_operation", {"type": "test"}):
        time.sleep(0.1)
    
    metrics = monitoring_system.metrics.get_metrics("test_operation_duration_seconds")
    assert len(metrics) == 1
    assert metrics[0].value >= 0.1
    assert metrics[0].labels["type"] == "test"

def test_system_status(monitoring_system):
    """Test system status retrieval."""
    status = monitoring_system.get_system_status()
    
    assert "timestamp" in status
    assert "system_metrics" in status
    assert "process_info" in status
    assert "recent_errors" in status

def test_metrics_export(monitoring_system, tmp_path):
    """Test metrics export functionality."""
    # Record some metrics
    monitoring_system.record_metric("test", 1.0)
    monitoring_system.record_metric("test", 2.0)
    
    # Export metrics
    export_path = tmp_path / "metrics.json"
    monitoring_system.export_metrics(export_path)
    
    # Verify exported data
    with open(export_path) as f:
        data = json.load(f)
    
    assert "test" in data
    assert len(data["test"]) == 2

def test_events_export(monitoring_system, tmp_path):
    """Test events export functionality."""
    # Record some events
    monitoring_system.record_event("test1", {"data": 1})
    monitoring_system.record_event("test2", {"data": 2})
    
    # Export events
    export_path = tmp_path / "events.json"
    monitoring_system.export_events(export_path)
    
    # Verify exported data
    with open(export_path) as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["name"] == "test1"
    assert data[1]["name"] == "test2"

def test_logging_setup(temp_log_file):
    """Test logging configuration."""
    monitoring_system = MonitoringSystem(log_path=temp_log_file)
    
    # Test log message
    test_message = "Test log message"
    monitoring_system.logger.info(test_message)
    
    # Verify message was logged to file
    with open(temp_log_file) as f:
        log_content = f.read()
    assert test_message in log_content

@patch('threading.Thread')
def test_background_worker(mock_thread, monitoring_system):
    """Test background worker initialization."""
    assert mock_thread.called
    assert monitoring_system._worker_queue is not None
    
    # Verify worker was started as daemon
    mock_thread.assert_called_with(
        target=monitoring_system._background_worker,
        daemon=True
    )