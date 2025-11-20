"""Configuration loader for the divergence scanner"""
import yaml
import os
from pathlib import Path


class Config:
    """Configuration manager"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def get(self, key: str, default=None):
        """Get configuration value by key (supports nested keys with dots)"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    def get_timeframes(self) -> list:
        """Get list of timeframes to analyze"""
        return self.config.get('timeframes', ['1d'])

    def get_indices(self) -> list:
        """Get list of indices to scan"""
        return self.config.get('indices', ['^GSPC'])

    def get_output_path(self) -> Path:
        """Get output directory path"""
        output_dir = Path(self.config.get('output', {}).get('directory', 'outputs'))
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_log_path(self) -> Path:
        """Get log directory path"""
        log_dir = Path(self.config.get('logging', {}).get('directory', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
