"""
LLM Logger for BookSouls

Centralized logging system for all LLM interactions including:
- Request/response pairs
- Performance metrics
- Error tracking
- Token usage
"""

import json
import os
import uuid
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path

from .config import get_logging_config, LoggingConfig


@dataclass
class LogEntry:
    """Represents a single LLM interaction log entry."""
    id: str
    timestamp: str
    model_type: str  # 'openai', 'ollama', etc.
    model_name: str
    request_type: str  # 'dialogue_extraction', 'character_analysis', etc.
    prompt: str
    response: str
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    response_time_ms: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMLogger:
    """
    Centralized logger for all LLM interactions in BookSouls.
    
    Features:
    - JSON-based structured logging
    - Automatic file rotation by date
    - Performance metrics tracking
    - Error logging and debugging support
    """
    
    def __init__(self, logs_dir: str = None, config: LoggingConfig = None):
        """
        Initialize the LLM logger.
        
        Args:
            logs_dir: Directory to store log files. If None, uses config or default.
            config: LoggingConfig instance. If None, uses global config.
        """
        # Get configuration
        self.config = config or get_logging_config()
        
        # Determine logs directory
        if logs_dir is not None:
            self.logs_dir = Path(logs_dir)
        else:
            self.logs_dir = self.config.get_logs_path()
        
        # Create logs directory if it doesn't exist
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different log types
        (self.logs_dir / "requests").mkdir(exist_ok=True)
        (self.logs_dir / "errors").mkdir(exist_ok=True)
        (self.logs_dir / "metrics").mkdir(exist_ok=True)
    
    def _get_log_filename(self, log_type: str = "requests") -> str:
        """Get filename for current date."""
        today = datetime.now().strftime("%Y-%m-%d")
        return str(self.logs_dir / log_type / f"{log_type}_{today}.jsonl")
    
    def _write_log_entry(self, entry: LogEntry, log_type: str = "requests"):
        """Write a log entry to the appropriate file."""
        # Check if logging is enabled for this type
        if log_type == "requests" and not self.config.enable_request_logging:
            return
        if log_type == "errors" and not self.config.enable_error_logging:
            return
        
        filename = self._get_log_filename(log_type)
        
        # Convert entry to JSON
        entry_dict = asdict(entry)
        
        # Truncate long fields if configured
        if entry_dict.get('prompt') and len(entry_dict['prompt']) > self.config.max_prompt_length:
            entry_dict['prompt'] = entry_dict['prompt'][:self.config.max_prompt_length] + "... [truncated]"
        
        if entry_dict.get('response') and len(entry_dict['response']) > self.config.max_response_length:
            entry_dict['response'] = entry_dict['response'][:self.config.max_response_length] + "... [truncated]"
        
        # Write to JSONL format (one JSON object per line)
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry_dict, ensure_ascii=False) + '\n')
    
    def log_request(self, 
                   model_type: str,
                   model_name: str,
                   request_type: str,
                   prompt: str,
                   response: str = None,
                   response_time_ms: int = None,
                   token_count_input: int = None,
                   token_count_output: int = None,
                   temperature: float = None,
                   max_tokens: int = None,
                   error: str = None,
                   metadata: Dict[str, Any] = None) -> str:
        """
        Log an LLM request/response pair.
        
        Args:
            model_type: Type of model ('openai', 'ollama', etc.)
            model_name: Specific model name (e.g., 'gpt-4o-mini', 'llama3.1')
            request_type: Type of request ('dialogue_extraction', 'character_analysis', etc.)
            prompt: The input prompt sent to the model
            response: The model's response (optional if logging before response)
            response_time_ms: Response time in milliseconds
            token_count_input: Number of input tokens
            token_count_output: Number of output tokens
            temperature: Model temperature setting
            max_tokens: Max tokens setting
            error: Error message if request failed
            metadata: Additional metadata (chapter_num, section_id, etc.)
            
        Returns:
            Unique ID for this log entry
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        entry = LogEntry(
            id=entry_id,
            timestamp=timestamp,
            model_type=model_type,
            model_name=model_name,
            request_type=request_type,
            prompt=prompt,
            response=response or "",
            token_count_input=token_count_input,
            token_count_output=token_count_output,
            response_time_ms=response_time_ms,
            temperature=temperature,
            max_tokens=max_tokens,
            error=error,
            metadata=metadata or {}
        )
        
        # Write to requests log
        self._write_log_entry(entry, "requests")
        
        # Also write to errors log if there's an error
        if error:
            self._write_log_entry(entry, "errors")
        
        return entry_id
    
    def update_response(self, entry_id: str, response: str,
                       response_time_ms: int = None,
                       token_count_input: int = None,
                       token_count_output: int = None,
                       error: str = None):
        """
        Update a log entry with response information.
        
        This is useful when you want to log the request immediately
        but update it with the response later.
        
        Args:
            entry_id: ID returned from log_request()
            response: The model's response
            response_time_ms: Response time in milliseconds
            token_count_input: Number of input tokens (optional)
            token_count_output: Number of output tokens
            error: Error message if request failed
        """
        # For simplicity, we'll create a new entry with the same ID
        # In a production system, you might want to implement true updates
        filename = self._get_log_filename("requests")
        
        # Read existing entries and update the matching one
        try:
            updated_entries = []
            found = False
            
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry_dict = json.loads(line.strip())
                        if entry_dict['id'] == entry_id:
                            entry_dict['response'] = response
                            if token_count_input is not None:
                                entry_dict['token_count_input'] = token_count_input
                            if response_time_ms is not None:
                                entry_dict['response_time_ms'] = response_time_ms
                            if token_count_output is not None:
                                entry_dict['token_count_output'] = token_count_output
                            if error is not None:
                                entry_dict['error'] = error
                            found = True
                        updated_entries.append(entry_dict)
            
            if found:
                # Rewrite the file with updated entries
                with open(filename, 'w', encoding='utf-8') as f:
                    for entry_dict in updated_entries:
                        f.write(json.dumps(entry_dict, ensure_ascii=False) + '\n')
            
        except Exception as e:
            print(f"Warning: Failed to update log entry {entry_id}: {str(e)}")
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics for recent LLM usage.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with usage statistics
        """
        stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'avg_response_time_ms': 0,
            'requests_by_model': {},
            'requests_by_type': {},
            'error_summary': []
        }
        
        response_times = []
        
        # Look through recent log files
        for i in range(days):
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            date = date.replace(days=-i) if hasattr(date, 'replace') else date
            date_str = date.strftime("%Y-%m-%d")
            filename = str(self.logs_dir / "requests" / f"requests_{date_str}.jsonl")
            
            if not os.path.exists(filename):
                continue
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    for line in f:
                        entry = json.loads(line.strip())
                        
                        stats['total_requests'] += 1
                        
                        # Count success/failure
                        if entry.get('error'):
                            stats['failed_requests'] += 1
                        else:
                            stats['successful_requests'] += 1
                        
                        # Token counts
                        if entry.get('token_count_input'):
                            stats['total_input_tokens'] += entry['token_count_input']
                        if entry.get('token_count_output'):
                            stats['total_output_tokens'] += entry['token_count_output']
                        
                        # Response times
                        if entry.get('response_time_ms'):
                            response_times.append(entry['response_time_ms'])
                        
                        # Model usage
                        model = f"{entry['model_type']}:{entry['model_name']}"
                        stats['requests_by_model'][model] = stats['requests_by_model'].get(model, 0) + 1
                        
                        # Request type usage
                        req_type = entry['request_type']
                        stats['requests_by_type'][req_type] = stats['requests_by_type'].get(req_type, 0) + 1
                        
            except Exception as e:
                print(f"Warning: Failed to read log file {filename}: {str(e)}")
        
        # Calculate average response time
        if response_times:
            stats['avg_response_time_ms'] = sum(response_times) / len(response_times)
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = None):
        """
        Clean up log files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep logs for. If None, uses config default.
        """
        if days_to_keep is None:
            days_to_keep = self.config.days_to_keep
            
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for log_type in ["requests", "errors", "metrics"]:
            log_dir = self.logs_dir / log_type
            if not log_dir.exists():
                continue
            
            for log_file in log_dir.glob("*.jsonl"):
                try:
                    # Extract date from filename
                    filename = log_file.stem
                    date_part = filename.split('_')[-1]  # Get date part
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        print(f"Deleted old log file: {log_file}")
                        
                except Exception as e:
                    print(f"Warning: Failed to process log file {log_file}: {str(e)}")


# Global logger instance
_global_logger = None

def get_logger() -> LLMLogger:
    """Get the global LLM logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = LLMLogger()
    return _global_logger


# Convenience functions
def log_llm_request(model_type: str, model_name: str, request_type: str, 
                   prompt: str, **kwargs) -> str:
    """Convenience function to log an LLM request."""
    return get_logger().log_request(model_type, model_name, request_type, prompt, **kwargs)


def log_llm_response(entry_id: str, response: str, **kwargs):
    """Convenience function to update a log entry with response."""
    get_logger().update_response(entry_id, response, **kwargs)