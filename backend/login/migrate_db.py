from sqlalchemy import create_engine, Column, Integer, ForeignKey, MetaData, Table
from .database import SQLALCHEMY_DATABASE_URL

def run_migration():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    
    # Create metadata object
    metadata = MetaData()
    
    # Reflect the users table
    users = Table('users', metadata, autoload_with=engine)
    
    # Don't try to add the column if it already exists
    if 'last_used_identity_id' not in [c.name for c in users.columns]:
        # Add column to users table
        engine.execute('ALTER TABLE users ADD COLUMN last_used_identity_id INTEGER REFERENCES anonymous_identities(id)')
        
        print("Migration successful: Added last_used_identity_id to users table")
    else:
        print("Column already exists, no migration needed")

# This script can be run directly
if __name__ == "__main__":
    run_migration()