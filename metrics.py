"""
Metrics collection and monitoring module for the AIS system.

This module provides comprehensive metrics collection including:
- Performance metrics (response times, throughput)
- Resource utilization metrics
- Business metrics and KPIs
- Metrics aggregation and reporting
- Export capabilities for monitoring systems
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from statistics import mean, median, stdev, quantiles
import threading
from contextlib import asynccontextmanager
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_for_logging(value: str) -> str:
    """Sanitize string for safe logging by removing newlines and control characters."""
    if not isinstance(value, str):
        value = str(value)
    # Remove newlines, carriage returns, and other control characters
    return re.sub(r'[\r\n\x00-\x1f\x7f-\x9f]', '_', value)


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(Enum):
    """Metric category enumeration."""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    BUSINESS = "business"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    """Individual metric value."""
    value: Union[int, float]
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None


@dataclass
class Metric:
    """Metric definition and data."""
    name: str
    description: str
    metric_type: MetricType
    category: MetricCategory
    unit: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MetricSnapshot:
    """Snapshot of all metrics at a point in time."""
    timestamp: datetime
    metrics: Dict[str, Metric]
    summary: Dict[str, Any]


class MetricsCollector:
    """Main metrics collection class."""
    
    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, Metric] = {}
        self.max_history = max_history
        self.lock = threading.Lock()
        self.logger = logger
        self.start_time = time.time()
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default system metrics."""
        # Performance metrics
        self.register_metric(
            name="request_duration_seconds",
            description="Request duration in seconds",
            metric_type=MetricType.HISTOGRAM,
            category=MetricCategory.PERFORMANCE,
            unit="seconds"
        )
        
        self.register_metric(
            name="requests_total",
            description="Total number of requests",
            metric_type=MetricType.COUNTER,
            category=MetricCategory.PERFORMANCE
        )
        
        self.register_metric(
            name="requests_per_second",
            description="Requests per second",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.PERFORMANCE,
            unit="requests/sec"
        )
        
        # Resource metrics
        self.register_metric(
            name="memory_usage_bytes",
            description="Memory usage in bytes",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.RESOURCE,
            unit="bytes"
        )
        
        self.register_metric(
            name="cpu_usage_percent",
            description="CPU usage percentage",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.RESOURCE,
            unit="percent"
        )
        
        # System metrics
        self.register_metric(
            name="uptime_seconds",
            description="System uptime in seconds",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM,
            unit="seconds"
        )
        
        self.register_metric(
            name="active_connections",
            description="Number of active connections",
            metric_type=MetricType.GAUGE,
            category=MetricCategory.SYSTEM
        )
    
    def register_metric(self, name: str, description: str, metric_type: MetricType,
                       category: MetricCategory, unit: Optional[str] = None,
                       labels: Optional[Dict[str, str]] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Metric:
        """Register a new metric."""
        with self.lock:
            if name in self.metrics:
                self.logger.warning(f"Metric {sanitize_for_logging(name)} already exists, updating description")
                self.metrics[name].description = description
                return self.metrics[name]
            
            metric = Metric(
                name=name,
                description=description,
                metric_type=metric_type,
                category=category,
                unit=unit,
                labels=labels or {},
                metadata=metadata or {}
            )
            
            self.metrics[name] = metric
            self.logger.info(f"Registered metric: {sanitize_for_logging(name)}")
            return metric
    
    def record_value(self, metric_name: str, value: Union[int, float],
                    labels: Optional[Dict[str, str]] = None,
                    timestamp: Optional[datetime] = None) -> None:
        """Record a value for a metric."""
        if metric_name not in self.metrics:
            self.logger.warning(f"Metric {sanitize_for_logging(metric_name)} not found, creating default")
            self.register_metric(
                name=metric_name,
                description=f"Auto-created metric: {metric_name}",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CUSTOM
            )
        
        metric = self.metrics[metric_name]
        timestamp = timestamp or datetime.now()
        
        metric_value = MetricValue(
            value=value,
            timestamp=timestamp,
            labels=labels or {}
        )
        
        with self.lock:
            metric.values.append(metric_value)
            
            # Keep only the most recent values
            if len(metric.values) > self.max_history:
                metric.values.popleft()
    
    def increment_counter(self, metric_name: str, value: int = 1,
                        labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        if metric_name not in self.metrics:
            self.logger.warning(f"Counter metric {sanitize_for_logging(metric_name)} not found, creating")
            self.register_metric(
                name=metric_name,
                description=f"Auto-created counter: {metric_name}",
                metric_type=MetricType.COUNTER,
                category=MetricCategory.CUSTOM
            )
        
        # For counters, we need to get the last value and increment it
        metric = self.metrics[metric_name]
        last_value = 0
        
        if metric.values:
            last_value = metric.values[-1].value
        
        self.record_value(metric_name, last_value + value, labels)
    
    def set_gauge(self, metric_name: str, value: Union[int, float],
                  labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric to a specific value."""
        if metric_name not in self.metrics:
            self.logger.warning(f"Gauge metric {sanitize_for_logging(metric_name)} not found, creating")
            self.register_metric(
                name=metric_name,
                description=f"Auto-created gauge: {metric_name}",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CUSTOM
            )
        
        self.record_value(metric_name, value, labels)
    
    def record_histogram(self, metric_name: str, value: Union[int, float],
                        labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value for a histogram metric."""
        if metric_name not in self.metrics:
            self.logger.warning(f"Histogram metric {sanitize_for_logging(metric_name)} not found, creating")
            self.register_metric(
                name=metric_name,
                description=f"Auto-created histogram: {metric_name}",
                metric_type=MetricType.HISTOGRAM,
                category=MetricCategory.CUSTOM
            )
        
        self.record_value(metric_name, value, labels)
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        return self.metrics.get(name)
    
    def get_metric_value(self, name: str, default: Any = None) -> Any:
        """Get the current value of a metric."""
        metric = self.get_metric(name)
        if metric and metric.values:
            return metric.values[-1].value
        return default
    
    def get_metric_summary(self, name: str, window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get a summary of a metric over a time window."""
        metric = self.get_metric(name)
        if not metric:
            return {"error": f"Metric {name} not found"}
        
        # Filter values by time window if specified
        if window:
            cutoff_time = datetime.now() - window
            values = [v.value for v in metric.values if v.timestamp >= cutoff_time]
        else:
            values = [v.value for v in metric.values]
        
        if not values:
            return {"error": "No data available"}
        
        summary = {
            "name": name,
            "type": metric.metric_type.value,
            "category": metric.category.value,
            "unit": metric.unit,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": mean(values),
            "last_value": values[-1] if values else None,
            "last_timestamp": metric.values[-1].timestamp.isoformat() if metric.values else None
        }
        
        if metric.metric_type == MetricType.HISTOGRAM and len(values) > 1:
            try:
                summary["median"] = median(values)
                summary["std_dev"] = stdev(values) if len(values) > 1 else 0
                summary["percentiles"] = {
                    "25": quantiles(values, n=4)[0] if len(values) > 1 else values[0],
                    "50": median(values),
                    "75": quantiles(values, n=4)[2] if len(values) > 1 else values[0],
                    "95": quantiles(values, n=20)[18] if len(values) > 19 else values[-1],
                    "99": quantiles(values, n=100)[98] if len(values) > 99 else values[-1]
                }
            except ValueError as e:
                self.logger.warning(f"Error calculating statistics for {name}: {sanitize_for_logging(str(e))}")
                summary["median"] = values[-1] if values else 0
                summary["std_dev"] = 0
                summary["percentiles"] = {"50": values[-1] if values else 0}
        
        return summary
    
    def get_all_metrics_summary(self, window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "total_metrics": len(self.metrics),
            "metrics_by_category": defaultdict(int),
            "metrics_by_type": defaultdict(int),
            "metric_summaries": {}
        }
        
        for name, metric in self.metrics.items():
            summary["metrics_by_category"][metric.category.value] += 1
            summary["metrics_by_type"][metric.metric_type.value] += 1
            summary["metric_summaries"][name] = self.get_metric_summary(name, window)
        
        return summary
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for name, metric in self.metrics.items():
            if not metric.values:
                continue
            
            # Build labels string
            labels_str = ""
            if metric.labels:
                label_pairs = [f'{k}="{v}"' for k, v in metric.labels.items()]
                labels_str = "{" + ",".join(label_pairs) + "}"
            
            # Get current value
            current_value = metric.values[-1].value
            
            # Format based on metric type
            if metric.metric_type == MetricType.COUNTER:
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name}{labels_str} {current_value}")
            elif metric.metric_type == MetricType.GAUGE:
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name}{labels_str} {current_value}")
            elif metric.metric_type == MetricType.HISTOGRAM:
                # For histogram, we'll export as a gauge for now
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name}{labels_str} {current_value}")
        
        return "\n".join(lines)
    
    def export_json(self) -> Dict[str, Any]:
        """Export metrics in JSON format."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        for name, metric in self.metrics.items():
            data["metrics"][name] = {
                "description": metric.description,
                "type": metric.metric_type.value,
                "category": metric.category.value,
                "unit": metric.unit,
                "labels": metric.labels,
                "current_value": self.get_metric_value(name),
                "summary": self.get_metric_summary(name)
            }
        
        return data
    
    def clear_metrics(self, metric_name: Optional[str] = None) -> None:
        """Clear metrics data."""
        with self.lock:
            if metric_name:
                if metric_name in self.metrics:
                    self.metrics[metric_name].values.clear()
                    self.logger.info(f"Cleared metric: {sanitize_for_logging(metric_name)}")
                else:
                    self.logger.warning(f"Metric not found for clearing: {sanitize_for_logging(metric_name)}")
            else:
                for metric in self.metrics.values():
                    metric.values.clear()
                self.logger.info("Cleared all metrics")


class MetricsMiddleware:
    """Middleware for automatically collecting metrics from requests."""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.logger = logger
    
    @asynccontextmanager
    async def measure_request(self, endpoint: str, method: str = "GET"):
        """Context manager for measuring request metrics."""
        start_time = time.time()
        
        try:
            # Increment request counter
            self.collector.increment_counter("requests_total", labels={"endpoint": endpoint, "method": method})
            
            yield
            
            # Record successful request duration
            duration = time.time() - start_time
            self.collector.record_histogram("request_duration_seconds", duration,
                                          labels={"endpoint": endpoint, "method": method})
            
        except Exception as e:
            # Record failed request
            self.collector.increment_counter("request_errors_total", 
                                          labels={"endpoint": endpoint, "method": method, "error": str(e)})
            raise
        finally:
            # Update requests per second gauge
            self._update_requests_per_second()
    
    def _update_requests_per_second(self):
        """Update requests per second metric."""
        # This is a simplified calculation - in production you'd want a rolling window
        total_requests = self.collector.get_metric_value("requests_total", 0)
        uptime = time.time() - self.collector.start_time
        
        if uptime > 0:
            rps = total_requests / uptime
            self.collector.set_gauge("requests_per_second", rps)


# Global metrics collector instance
metrics_collector = MetricsCollector()
metrics_middleware = MetricsMiddleware(metrics_collector)


# Convenience functions
def record_metric(name: str, value: Union[int, float], **kwargs):
    """Record a metric value."""
    metrics_collector.record_value(name, value, **kwargs)


def increment_counter(name: str, value: int = 1, **kwargs):
    """Increment a counter metric."""
    metrics_collector.increment_counter(name, value, **kwargs)


def set_gauge(name: str, value: Union[int, float], **kwargs):
    """Set a gauge metric value."""
    metrics_collector.set_gauge(name, value, **kwargs)


def get_metric_summary(name: str, **kwargs):
    """Get a metric summary."""
    return metrics_collector.get_metric_summary(name, **kwargs)


def get_all_metrics(**kwargs):
    """Get all metrics summary."""
    return metrics_collector.get_all_metrics_summary(**kwargs)


if __name__ == "__main__":
    def main():
        """Test the metrics collection system."""
        print("Testing metrics collection system...")
        
        # Record some test metrics
        record_metric("test_counter", 1)
        increment_counter("test_counter", 5)
        set_gauge("test_gauge", 42.5)
        record_metric("test_histogram", 0.1)
        record_metric("test_histogram", 0.2)
        record_metric("test_histogram", 0.15)
        
        # Get summaries
        print("\nTest counter summary:")
        print(json.dumps(get_metric_summary("test_counter"), indent=2))
        
        print("\nTest histogram summary:")
        print(json.dumps(get_metric_summary("test_histogram"), indent=2))
        
        print("\nAll metrics summary:")
        print(json.dumps(get_all_metrics(), indent=2))
        
        print("\nPrometheus export:")
        print(metrics_collector.export_prometheus())
    
    asyncio.run(main())
