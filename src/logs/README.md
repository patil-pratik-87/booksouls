# BookSouls LLM Logging System

A comprehensive logging system for tracking all LLM interactions across the BookSouls application, including request/response pairs, performance metrics, and error tracking.

## Features

- **Configurable Logging**: Customizable log directories, retention policies, and behavior
- **Structured Logging**: JSON-based logs with comprehensive metadata
- **Performance Monitoring**: Response times, token usage, and throughput metrics
- **Error Tracking**: Detailed error logs with context for debugging
- **Multiple LLM Support**: Works with OpenAI, Ollama, and other LLM providers
- **Automatic File Rotation**: Daily log files with configurable retention
- **Usage Analytics**: Built-in statistics and reporting
- **Default Location**: Logs stored in `./data/logs/` by default

## Directory Structure

```
src/logs/                    # Source code
├── __init__.py             # Main exports
├── llm_logger.py           # Core logging functionality
├── metrics.py              # Performance metrics collection
├── config.py               # Configuration system
├── example_usage.py        # Usage examples and demo
├── example_config.py       # Configuration examples
└── README.md               # This file

data/logs/                   # Default log storage location (configurable)
├── requests/               # Daily request/response logs
├── errors/                 # Error-specific logs
└── metrics/                # Performance metrics logs
```

## Quick Start

### Basic Usage (Default Configuration)

By default, logs are stored in `./data/logs/` relative to your project root.

```python
from src.logs import log_llm_request, log_llm_response

# Log a request (logs to ./data/logs/ by default)
log_id = log_llm_request(
    model_type="openai",
    model_name="gpt-4o-mini", 
    request_type="dialogue_extraction",
    prompt="Extract dialogue from this text...",
    temperature=0.7,
    max_tokens=1000
)

# Log the response
log_llm_response(
    log_id,
    response="Generated response text...",
    response_time_ms=1500,
    token_count_output=25
)
```

### Custom Configuration

```python
from src.logs import configure_logging, LLMLogger

# Configure custom settings
configure_logging(
    logs_dir="./custom_logs",  # Custom directory
    days_to_keep=14,           # Keep logs for 2 weeks
    max_prompt_length=5000     # Limit prompt size in logs
)

# Now all logging uses these settings
logger = LLMLogger()
```

### Using the Logger Class

```python
from src.logs import LLMLogger

logger = LLMLogger()

# Log request and response in one call
log_id = logger.log_request(
    model_type="ollama",
    model_name="llama3.1:8b",
    request_type="character_analysis", 
    prompt="Analyze this character...",
    response="Character analysis results...",
    response_time_ms=2300,
    token_count_input=150,
    token_count_output=45,
    temperature=0.5,
    error=None,  # Optional error message
    metadata={"chapter": 1, "section": "intro"}
)
```

### Performance Timing

```python
from src.logs import LLMTimer

# Time an operation
with LLMTimer("dialogue_extraction") as timer:
    # Your LLM call here
    response = model.generate(prompt)

print(f"Operation took {timer.get_elapsed_ms():.2f}ms")
```

### Getting Usage Statistics

```python
from src.logs import LLMLogger

logger = LLMLogger()
stats = logger.get_stats(days=7)

print(f"Total requests: {stats['total_requests']}")
print(f"Average response time: {stats['avg_response_time_ms']:.2f}ms")
print(f"Requests by model: {stats['requests_by_model']}")
```

## Integration Examples

### Dialogue Chunker Integration

The logging system is already integrated into the `DialogueChunker` class:

```python
# dialogue_chunker.py automatically logs all LLM calls
chunker = DialogueChunker(config)
dialogue_index = chunker.create_dialogue_index(chapters)
# All LLM requests/responses are automatically logged
```

### Base Agent Integration

Character agents automatically log all LLM interactions:

```python
# base_agent.py wraps LLM calls with logging
agent = BaseAgent(config, book_context)
response = agent.process_user_input("Hello")
# Agent interactions are automatically logged
```

## Log File Format

### Request Logs (`requests/requests_YYYY-MM-DD.jsonl`)

Each line contains a JSON object with:

```json
{
  "id": "uuid-string",
  "timestamp": "2024-01-15T10:30:45.123456", 
  "model_type": "openai",
  "model_name": "gpt-4o-mini",
  "request_type": "dialogue_extraction",
  "prompt": "Extract dialogue from...",
  "response": "Generated response...",
  "token_count_input": 150,
  "token_count_output": 25,
  "response_time_ms": 1500,
  "temperature": 0.7,
  "max_tokens": 1000,
  "error": null,
  "metadata": {"chapter": 1, "section": "intro"}
}
```

### Error Logs (`errors/errors_YYYY-MM-DD.jsonl`)

Same format as request logs, but only entries with errors.

### Metrics Logs (`metrics/metrics_YYYY-MM-DD.jsonl`)

Performance metrics:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "metric_name": "response_time", 
  "value": 1500.0,
  "unit": "ms",
  "metadata": {"model": "gpt-4o-mini", "operation": "dialogue_extraction"}
}
```

## Configuration Options

### Available Configuration Settings

```python
from src.logs import configure_logging

configure_logging(
    # Directory settings
    logs_dir="./data/logs",           # Where to store logs
    
    # Retention settings  
    days_to_keep=30,                  # How long to keep log files
    
    # Logging behavior
    enable_request_logging=True,       # Log LLM requests/responses
    enable_error_logging=True,         # Log errors
    enable_metrics_logging=True,       # Log performance metrics
    
    # Performance settings
    max_prompt_length=10000,          # Truncate long prompts
    max_response_length=50000         # Truncate long responses
)
```

### Environment-Based Configuration

```python
import os
from src.logs import configure_logging

# Configure based on environment
env = os.getenv('ENVIRONMENT', 'development')

if env == 'production':
    configure_logging(
        logs_dir="/var/log/booksouls",
        days_to_keep=90,
        max_prompt_length=1000
    )
else:
    configure_logging(
        logs_dir="./dev_logs", 
        days_to_keep=7,
        max_prompt_length=10000
    )
```

### Quick Directory Change

```python
from src.logs import set_logs_dir

# Quickly change logs directory
set_logs_dir("./my_custom_logs")
```

### Custom Log Directory (Per Logger)

```python
from src.logs import LLMLogger

# Use custom directory for this logger only
logger = LLMLogger(logs_dir="/path/to/custom/logs")
```

### Log Cleanup

```python
logger = LLMLogger()

# Clean up logs older than specified days (uses config default if not specified)
logger.cleanup_old_logs()  # Uses config.days_to_keep
logger.cleanup_old_logs(days_to_keep=30)  # Override with custom value
```

## Request Types

The system tracks different types of LLM requests:

- `dialogue_extraction`: Extracting dialogue from text chunks
- `character_analysis`: Analyzing character traits and development
- `agent_interaction`: Character agent conversations
- `narrative_generation`: Story or content generation
- `custom`: Custom request types for specific use cases

## Performance Monitoring

### Built-in Metrics

- Response time (ms)
- Token usage (input/output)
- Request success/failure rates
- Model usage distribution
- Request type distribution

### Custom Metrics

```python
from src.logs import LLMMetrics

metrics = LLMMetrics()
metrics.record_metric("custom_metric", 42.0, "units", {"context": "info"})
```

## Error Handling

Errors are automatically logged with full context:

- Exception message and type
- Request parameters that caused the error
- Timestamp and model information
- Additional metadata for debugging

## Best Practices

1. **Always log LLM requests**: Use the integrated logging in existing classes
2. **Include metadata**: Add context like chapter, section, or operation type
3. **Monitor performance**: Check response times and token usage regularly
4. **Clean up old logs**: Implement log rotation based on your needs
5. **Use request types**: Categorize different types of LLM operations

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure write access to the logs directory
2. **Missing logs**: Check that the logging imports are correct
3. **Performance issues**: Monitor log file sizes and clean up old files

### Debug Mode

Set verbose logging in your chunker config:

```python
config = DialogueChunkerConfig(verbose=True)
```

## Running the Demo

```bash
cd src/logs
python example_usage.py        # Basic usage demo
python example_config.py       # Configuration examples
```

The demo will create sample logs in `./data/logs/` (or configured directory) and demonstrate all features of the logging system.

## Configuration Examples

See `src/logs/example_config.py` for detailed examples of:
- Default configuration (logs to `./data/logs/`)
- Custom directory configuration  
- Production vs development settings
- Environment-based configuration
- Minimal logging (errors only)
- Per-logger custom configuration