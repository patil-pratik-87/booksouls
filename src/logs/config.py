"""
Configuration for BookSouls LLM Logging System

Provides configurable settings for log directories, retention policies,
and logging behavior.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LoggingConfig:
    """Configuration for the LLM logging system."""
    
    # Directory settings
    logs_dir: Optional[str] = None  # Default will be ./data/logs
    
    # File retention settings
    days_to_keep: int = 30  # How many days to keep log files
    
    # Logging behavior
    enable_request_logging: bool = True
    enable_error_logging: bool = True
    enable_metrics_logging: bool = True
    
    # Performance settings
    max_prompt_length: int = 10000  # Truncate very long prompts
    max_response_length: int = 50000  # Truncate very long responses
    
    def __post_init__(self):
        """Set default logs directory if not provided."""
        if self.logs_dir is None:
            # Default to ./data/logs relative to project root
            # Find project root by looking for common project files
            current = Path(__file__).parent
            project_root = current
            
            # Walk up directories to find project root
            for _ in range(5):  # Max 5 levels up
                if any((project_root / marker).exists() for marker in ['.git', 'pyproject.toml', 'setup.py', 'requirements.txt']):
                    break
                project_root = project_root.parent
            else:
                # Fallback: assume we're in src/logs, so go up 2 levels
                project_root = current.parent.parent
            
            self.logs_dir = str(project_root / "data" / "logs")
    
    def get_logs_path(self) -> Path:
        """Get the logs directory as a Path object."""
        return Path(self.logs_dir)


# Global configuration instance
_global_config = None


def get_logging_config() -> LoggingConfig:
    """Get the global logging configuration."""
    global _global_config
    if _global_config is None:
        _global_config = LoggingConfig()
    return _global_config


def set_logging_config(config: LoggingConfig):
    """Set the global logging configuration."""
    global _global_config
    _global_config = config


def configure_logging(logs_dir: str = None, 
                     days_to_keep: int = 30,
                     enable_request_logging: bool = True,
                     enable_error_logging: bool = True,
                     enable_metrics_logging: bool = True,
                     **kwargs) -> LoggingConfig:
    """
    Configure the logging system with custom settings.
    
    Args:
        logs_dir: Custom logs directory path
        days_to_keep: Number of days to keep log files
        enable_request_logging: Whether to log LLM requests/responses
        enable_error_logging: Whether to log errors
        enable_metrics_logging: Whether to log performance metrics
        **kwargs: Additional configuration options
        
    Returns:
        The configured LoggingConfig instance
    """
    config = LoggingConfig(
        logs_dir=logs_dir,
        days_to_keep=days_to_keep,
        enable_request_logging=enable_request_logging,
        enable_error_logging=enable_error_logging,
        enable_metrics_logging=enable_metrics_logging,
        **kwargs
    )
    
    set_logging_config(config)
    return config


def get_logs_dir() -> str:
    """Get the current logs directory path."""
    return get_logging_config().logs_dir


def set_logs_dir(logs_dir: str):
    """Set a custom logs directory."""
    config = get_logging_config()
    config.logs_dir = logs_dir
    set_logging_config(config)