# Configuration module - direct import to avoid circular imports
import os
import sys

# Get the parent directory and import config directly
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_file = os.path.join(parent_dir, 'config.py')

# Load the config module directly
spec = __import__('importlib.util', fromlist=['spec_from_file_location']).spec_from_file_location("config_module", config_file)
config_module = __import__('importlib.util', fromlist=['module_from_spec']).module_from_spec(spec)
spec.loader.exec_module(config_module)

# Import the classes
Config = config_module.Config
DEFAULT_SETTINGS = config_module.DEFAULT_SETTINGS