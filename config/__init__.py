# Configuration module
# Import from the parent config.py file
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config, DEFAULT_SETTINGS