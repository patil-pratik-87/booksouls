import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestConfig:
    """Test configuration settings."""
    
    # API settings
    use_openai: bool = True
    openai_api_key: Optional[str] = None
    
    # Vector store settings  
    base_persist_dir: str = "./vector_stores"
    
    # Test data settings
    data_base_dir: str = "../data/outputs"
    skip_indexing_if_exists: bool = True
    
    # Query settings
    default_n_results: int = 3
    max_results_display: int = 5
    content_preview_length: int = 150
    
    # Test behavior settings
    interactive_mode: bool = False
    verbose_output: bool = True
    auto_load_latest_data: bool = True
    
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestConfig':
        """Create config from dictionary."""
        return cls(**data)


def load_test_config(config_path: Optional[str] = None) -> TestConfig:
    """
    Load test configuration from file or environment.
    
    Args:
        config_path: Path to config file. If None, looks for default locations.
        
    Returns:
        TestConfig instance with loaded settings.
    """
    config = TestConfig()
    
    # Default config file locations
    if config_path is None:
        test_dir = Path(__file__).parent.parent
        possible_paths = [
            test_dir / "config" / "test_config.json",
            test_dir / "test_config.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
    
    # Load from file if exists
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Update config with file values
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    # Override with environment variables
    env_mappings = {
        'OPENAI_API_KEY': 'openai_api_key',
        'TEST_USE_OPENAI': 'use_openai',
        'TEST_PERSIST_DIR': 'base_persist_dir',
        'TEST_DATA_DIR': 'data_base_dir',
        'TEST_VERBOSE': 'verbose_output',
        'TEST_INTERACTIVE': 'interactive_mode',
    }
    
    for env_var, config_attr in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Convert string values to appropriate types
            if config_attr in ['use_openai', 'verbose_output', 'interactive_mode', 'skip_indexing_if_exists', 'auto_load_latest_data']:
                env_value = env_value.lower() in ('true', '1', 'yes', 'on')
            elif config_attr in ['default_n_results', 'max_results_display', 'content_preview_length']:
                try:
                    env_value = int(env_value)
                except ValueError:
                    continue
            
            setattr(config, config_attr, env_value)
    
    return config


def save_test_config(config: TestConfig, config_path: str) -> None:
    """
    Save test configuration to file.
    
    Args:
        config: TestConfig instance to save.
        config_path: Path where to save the config file.
    """
    config_dir = os.path.dirname(config_path)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.to_dict(), f, indent=2)


def get_default_test_config_path() -> str:
    """Get the default test config file path."""
    test_dir = Path(__file__).parent.parent
    return str(test_dir / "config" / "test_config.json")


if __name__ == "__main__":
    # Demo usage
    config = load_test_config()
    print("Current test configuration:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")