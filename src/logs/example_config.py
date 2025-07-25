#!/usr/bin/env python3
"""
Configuration examples for BookSouls LLM Logging System.

Shows different ways to configure the logging system for various use cases.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from logs import configure_logging, LLMLogger, get_logging_config, set_logs_dir


def example_default_config():
    """Example: Using default configuration (logs to ./data/logs)."""
    print("=== Default Configuration ===")
    
    # Default config automatically uses ./data/logs
    logger = LLMLogger()
    
    config = get_logging_config()
    print(f"Default logs directory: {config.logs_dir}")
    print(f"Days to keep logs: {config.days_to_keep}")
    print(f"Request logging enabled: {config.enable_request_logging}")
    print(f"Error logging enabled: {config.enable_error_logging}")
    print(f"Metrics logging enabled: {config.enable_metrics_logging}")


def example_custom_directory():
    """Example: Custom logs directory."""
    print("\n=== Custom Directory Configuration ===")
    
    # Configure custom directory
    configure_logging(logs_dir="./custom_logs")
    
    logger = LLMLogger()
    config = get_logging_config()
    print(f"Custom logs directory: {config.logs_dir}")
    
    # Alternative: Set directory directly
    set_logs_dir("./another_custom_dir")
    print(f"Updated logs directory: {get_logging_config().logs_dir}")


def example_production_config():
    """Example: Production configuration with longer retention."""
    print("\n=== Production Configuration ===")
    
    configure_logging(
        logs_dir="/var/log/booksouls",  # System logs directory
        days_to_keep=90,  # Keep logs for 3 months
        max_prompt_length=5000,  # Limit prompt size in logs
        max_response_length=20000  # Limit response size in logs
    )
    
    config = get_logging_config()
    print(f"Production logs directory: {config.logs_dir}")
    print(f"Log retention: {config.days_to_keep} days")
    print(f"Max prompt length: {config.max_prompt_length} chars")
    print(f"Max response length: {config.max_response_length} chars")


def example_development_config():
    """Example: Development configuration with verbose logging."""
    print("\n=== Development Configuration ===")
    
    configure_logging(
        logs_dir="./dev_logs",
        days_to_keep=7,  # Keep logs for 1 week only
        max_prompt_length=50000,  # Keep full prompts for debugging
        max_response_length=100000  # Keep full responses for debugging
    )
    
    config = get_logging_config()
    print(f"Development logs directory: {config.logs_dir}")
    print(f"Log retention: {config.days_to_keep} days")
    print(f"Max prompt length: {config.max_prompt_length} chars")
    print(f"Max response length: {config.max_response_length} chars")


def example_minimal_config():
    """Example: Minimal logging (errors only)."""
    print("\n=== Minimal Configuration ===")
    
    configure_logging(
        logs_dir="./minimal_logs",
        enable_request_logging=False,  # Disable request logs
        enable_metrics_logging=False,  # Disable metrics
        enable_error_logging=True  # Keep only error logs
    )
    
    config = get_logging_config()
    print(f"Minimal logs directory: {config.logs_dir}")
    print(f"Request logging: {config.enable_request_logging}")
    print(f"Error logging: {config.enable_error_logging}")
    print(f"Metrics logging: {config.enable_metrics_logging}")


def example_logger_with_custom_config():
    """Example: Creating logger with specific configuration."""
    print("\n=== Logger with Custom Config ===")
    
    from logs.config import LoggingConfig
    
    # Create custom config without setting it globally
    custom_config = LoggingConfig(
        logs_dir="./temp_logs",
        days_to_keep=1,  # Very short retention
        enable_metrics_logging=False
    )
    
    # Create logger with this specific config
    logger = LLMLogger(config=custom_config)
    
    print(f"Custom logger directory: {logger.logs_dir}")
    print(f"Custom config days to keep: {custom_config.days_to_keep}")
    print(f"Metrics enabled: {custom_config.enable_metrics_logging}")


def example_environment_based_config():
    """Example: Configuration based on environment."""
    print("\n=== Environment-Based Configuration ===")
    
    import os
    
    # Get environment (defaults to 'development')
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        configure_logging(
            logs_dir="/var/log/booksouls",
            days_to_keep=30,
            max_prompt_length=1000,
            max_response_length=5000
        )
    elif env == 'staging':
        configure_logging(
            logs_dir="./staging_logs",
            days_to_keep=14,
            max_prompt_length=2000,
            max_response_length=10000
        )
    else:  # development
        configure_logging(
            logs_dir="./dev_logs",
            days_to_keep=7,
            max_prompt_length=10000,
            max_response_length=50000
        )
    
    config = get_logging_config()
    print(f"Environment: {env}")
    print(f"Logs directory: {config.logs_dir}")
    print(f"Log retention: {config.days_to_keep} days")


if __name__ == "__main__":
    print("BookSouls LLM Logging Configuration Examples")
    print("=" * 50)
    
    try:
        example_default_config()
        example_custom_directory()
        example_production_config()
        example_development_config()
        example_minimal_config()
        example_logger_with_custom_config()
        example_environment_based_config()
        
        print("\n✅ All configuration examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Configuration example failed: {str(e)}")
        import traceback
        traceback.print_exc()