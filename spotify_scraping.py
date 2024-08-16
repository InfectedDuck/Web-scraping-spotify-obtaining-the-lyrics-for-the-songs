import requests
import base64
import csv
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Spotify API credentials
client_id = '0e6355ff7ebe4b6b969c321b508358e0'
client_secret = '11eabb27eecd4941bdf326717b9fb7bb'

# Encode credentials
encoded_credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()

# Obtain access token
auth_url = 'https://accounts.spotify.com/api/token'
auth_data = {
    'grant_type': 'client_credentials'
}
auth_headers = {
    'Authorization': f'Basic {encoded_credentials}'
}
response = requests.post(auth_url, data=auth_data, headers=auth_headers)
access_token = response.json().get('access_token')

# Fetch playlist tracks
playlist_id = '4geijLsFwxshTAku5IBVqs'
playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
headers = {
    'Authorization': f'Bearer {access_token}'
}
response = requests.get(playlist_url, headers=headers)
tracks = response.json().get('items')

# Set up SQLAlchemy
DATABASE_URL = 'sqlite:///songs.db'
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
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
Base.metadata.create_all(bind=engine)

# Insert data into database and write to CSV
def insert_songs_and_export_csv(tracks, csv_file='songs.csv'):
    session = SessionLocal()
    song_list = []

    for item in tracks:
        track = item.get('track')
        song_name = track.get('name')
        song_artist = ', '.join(artist.get('name') for artist in track.get('artists'))
        
        # Handling date formatting
        added_date_str = item.get('added_at')
        added_date = datetime.strptime(added_date_str, '%Y-%m-%dT%H:%M:%SZ')

        # Save the song to the database
        song = Song(
            id=track.get('id'),
            title=song_name,
            author=song_artist,
            added_date=added_date
        )
        session.add(song)

        # Prepare data for CSV
        song_list.append({
            'ID': track.get('id'),
            'Title': song_name,
            'Author': song_artist,
            'Added Date': added_date.strftime('%Y-%m-%d %H:%M:%S')  # Ensures proper date format
        })

    session.commit()
    session.close()

    # Write data to CSV with UTF-8 encoding
    with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ID', 'Title', 'Author', 'Added Date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(song_list)

    print(f"Data exported to {csv_file}")

# Call the function to insert songs and export to CSV
insert_songs_and_export_csv(tracks)
