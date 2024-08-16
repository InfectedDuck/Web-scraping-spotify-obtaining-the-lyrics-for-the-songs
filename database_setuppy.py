import os
import sys
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print(sys.getdefaultencoding())
# Set up SQLAlchemy
DATABASE_URL = 'sqlite:///songs.db'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Song model
class Song(Base):
    __tablename__ = 'songs'

    id = Column(String, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    author = Column(Text, nullable=False)
    added_date = Column(DateTime, nullable=False)

# Create tables
def create_db(replace_existing=False):
    if replace_existing:
        # Remove the existing database file if it exists
        if os.path.exists('songs.db'):
            os.remove('songs.db')
            print("Existing database file removed")
    
    # Create new database and tables
    Base.metadata.create_all(bind=engine)
    print("Database and tables created")

if __name__ == "__main__":
    create_db(replace_existing=True)
