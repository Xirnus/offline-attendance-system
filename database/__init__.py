from .connection import get_db_connection
from .operations import *

def init_db():
    """Initialize database with all required tables"""
    from .models import create_all_tables
    create_all_tables()

def migrate_database():
    """Apply database migrations"""
    from .models import migrate_tables
    migrate_tables()