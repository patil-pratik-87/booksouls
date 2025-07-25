#!/usr/bin/env python3
"""
Example usage of the BookSouls LLM logging system.

This script demonstrates how to use the logging system and shows
what kind of logs are generated during LLM operations.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from logs import LLMLogger, log_llm_request, log_llm_response, LLMTimer, LLMMetrics, configure_logging


def demonstrate_basic_logging():
    """Demonstrate basic request/response logging."""
    print("=== Basic Logging Demo ===")
    
    # Get logger instance
    logger = LLMLogger()
    
    # Example: Log a dialogue extraction request
    log_id = logger.log_request(
        model_type="openai",
        model_name="gpt-4o-mini",
        request_type="dialogue_extraction",
        prompt="Extract dialogue from: 'Hello,' said John. 'How are you?'",
        temperature=0.7,
        max_tokens=1000,
        metadata={"chapter": 1, "section": "intro"}
    )
    
    print(f"Logged request with ID: {log_id}")
    
    # Simulate a response (in real usage, this would come from the LLM)
    simulated_response = '{"dialogues": [{"speaker": "John", "dialogue": "Hello, how are you?"}]}'
    
    # Log the response
    logger.update_response(
        log_id,
        simulated_response,
        response_time_ms=1500,
        token_count_output=25
    )
    
    print("Updated log entry with response data")


def demonstrate_convenience_functions():
    """Demonstrate convenience functions."""
    print("\n=== Convenience Functions Demo ===")
    
    # Using convenience functions
    log_id = log_llm_request(
        model_type="ollama",
        model_name="llama3.1:8b",
        request_type="character_analysis",
        prompt="Analyze the character traits of Gandalf",
        temperature=0.5,
        max_tokens=500
    )
    
    print(f"Logged request with convenience function: {log_id}")
    
    # Log response
    log_llm_response(
        log_id,
        "Gandalf shows wisdom, courage, and magical prowess...",
        response_time_ms=2300,
        token_count_output=45
    )
    
    print("Updated with convenience function")


def demonstrate_timer():
    """Demonstrate the LLM timer for performance monitoring."""
    print("\n=== Timer Demo ===")
    
    # Using the timer context manager
    with LLMTimer("test_operation", {"test": "demo"}) as timer:
        # Simulate some work
        import time
        time.sleep(0.1)  # 100ms simulated work
    
    print(f"Timer recorded operation taking {timer.get_elapsed_ms():.2f}ms")


def demonstrate_metrics():
    """Demonstrate metrics collection."""
    print("\n=== Metrics Demo ===")
    
    metrics = LLMMetrics()
    
    # Record some sample metrics
    metrics.record_metric("response_time", 1200, "ms", {"model": "gpt-4o-mini"})
    metrics.record_metric("token_rate", 15.5, "tokens/sec", {"model": "gpt-4o-mini"})
    metrics.record_metric("response_time", 2800, "ms", {"model": "llama3.1"})
    
    print("Recorded sample metrics")
    
    # Get metric summary
    summary = metrics.get_metric_summary("response_time", days=1)
    print(f"Response time summary: {summary}")


def demonstrate_stats():
    """Demonstrate getting usage statistics."""
    print("\n=== Statistics Demo ===")
    
    logger = LLMLogger()
    stats = logger.get_stats(days=1)
    
    print("Current usage statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Successful: {stats['successful_requests']}")
    print(f"  Failed: {stats['failed_requests']}")
    print(f"  Total input tokens: {stats['total_input_tokens']}")
    print(f"  Total output tokens: {stats['total_output_tokens']}")
    print(f"  Average response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"  Requests by model: {stats['requests_by_model']}")
    print(f"  Requests by type: {stats['requests_by_type']}")


def demonstrate_configuration():
    """Demonstrate configurable logging system."""
    print("\n=== Configuration Demo ===")
    
    # Configure logging to use custom directory
    configure_logging(
        logs_dir="./demo_logs",
        days_to_keep=7,
        max_prompt_length=100  # Very short for demo
    )
    
    # Test with truncated prompt
    log_id = log_llm_request(
        model_type="demo",
        model_name="demo-model",
        request_type="demo",
        prompt="This is a very long prompt that will be truncated because it exceeds the configured limit of 100 characters in the configuration settings",
        temperature=0.5
    )
    
    log_llm_response(log_id, "Short response")
    print("Logged request with prompt truncation")


def show_log_files():
    """Show the structure of created log files."""
    print("\n=== Log Files Structure ===")
    
    logger = LLMLogger()
    logs_dir = logger.logs_dir
    
    print(f"Logs directory: {logs_dir}")
    print(f"  (Default is ./data/logs, configurable)")
    
    for subdir in ["requests", "errors", "metrics"]:
        subdir_path = logs_dir / subdir
        if subdir_path.exists():
            files = list(subdir_path.glob("*.jsonl"))
            print(f"  {subdir}/: {len(files)} files")
            for file in files[:3]:  # Show first 3 files
                print(f"    - {file.name}")
            if len(files) > 3:
                print(f"    - ... and {len(files) - 3} more")
        else:
            print(f"  {subdir}/: (no files yet)")


if __name__ == "__main__":
    print("BookSouls LLM Logging System Demo")
    print("=" * 40)
    
    try:
        demonstrate_basic_logging()
        demonstrate_convenience_functions()
        demonstrate_timer()
        demonstrate_metrics()
        demonstrate_configuration()
        demonstrate_stats()
        show_log_files()
        
        print("\n✅ Demo completed successfully!")
        print(f"Check the logs directory at: {Path(__file__).parent}")
        
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()