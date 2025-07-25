"""
LLM Metrics Collection for BookSouls

Provides performance monitoring and analytics for LLM usage.
"""

import json
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config import get_logging_config, LoggingConfig


@dataclass
class MetricEntry:
    """Represents a performance metric entry."""
    timestamp: str
    metric_name: str
    value: float
    unit: str
    metadata: Dict[str, Any]


class LLMMetrics:
    """
    Collects and analyzes performance metrics for LLM operations.
    """
    
    def __init__(self, logs_dir: str = None, config: LoggingConfig = None):
        """Initialize metrics collector."""
        # Get configuration
        self.config = config or get_logging_config()
        
        # Determine logs directory
        if logs_dir is not None:
            self.logs_dir = Path(logs_dir)
        else:
            self.logs_dir = self.config.get_logs_path()
        
        self.metrics_dir = self.logs_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_metrics_filename(self) -> str:
        """Get filename for current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        return str(self.metrics_dir / f"metrics_{today}.jsonl")
    
    def record_metric(self, name: str, value: float, unit: str = "", 
                     metadata: Dict[str, Any] = None):
        """
        Record a performance metric.
        
        Args:
            name: Metric name (e.g., 'response_time', 'token_rate')
            value: Metric value
            unit: Unit of measurement (e.g., 'ms', 'tokens/sec')
            metadata: Additional context
        """
        # Check if metrics logging is enabled
        if not self.config.enable_metrics_logging:
            return
            
        entry = MetricEntry(
            timestamp=datetime.now().isoformat(),
            metric_name=name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        
        filename = self._get_metrics_filename()
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + '\n')
    
    def get_metric_summary(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """
        Get summary statistics for a specific metric.
        
        Args:
            metric_name: Name of the metric to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary with min, max, avg, count statistics
        """
        values = []
        
        for i in range(days):
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            # Simple date arithmetic (in production, use proper date library)
            date_str = date.strftime("%Y-%m-%d")
            filename = str(self.metrics_dir / f"metrics_{date_str}.jsonl")
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        if entry['metric_name'] == metric_name:
                            values.append(entry['value'])
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Warning: Failed to read metrics file {filename}: {str(e)}")
        
        if not values:
            return {'count': 0}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'total': sum(values)
        }


class LLMTimer:
    """Context manager for timing LLM operations."""
    
    def __init__(self, operation_name: str, metadata: Dict[str, Any] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time = None
        self.metrics = LLMMetrics()
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.metrics.record_metric(
                f"{self.operation_name}_duration",
                duration_ms,
                "ms",
                self.metadata
            )
    
    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0
        return (time.time() - self.start_time) * 1000