import requests
import base64
import csv
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from googleapiclient.discovery import build
import yt_dlp
import os
import logging

# Spotify API credentials
client_id = '0e6355ff7ebe4b6b969c321b508358e0'
client_secret = '11eabb27eecd4941bdf326717b9fb7bb'

# YouTube API credentials
youtube_api_key = 'AIzaSyA8KhPnTIzFGkk2qjeRIgoWgrXY_bxvL7A'

# Set up logging
logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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

    for item in tracks[:5]:  # Limit to the first 5 songs
        track = item.get('track')
        song_name = track.get('name')
        song_artist = ', '.join(artist.get('name') for artist in track.get('artists'))
        
        # Handling date formatting
        added_date_str = item.get('added_at')
        added_date = datetime.strptime(added_date_str, '%Y-%m-%dT%H:%M:%SZ')

        # Check if the song is already in the database
        existing_song = session.query(Song).filter(Song.title == song_name).first()
        if existing_song:
            continue

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

    # Return list of tuples (title, author) for YouTube search
    return [(song['Title'], song['Author']) for song in song_list]

# Search YouTube for the given titles and download the videos
def search_and_download_youtube_videos(titles_and_authors, download_folder='videos'):
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    for title, author in titles_and_authors:
        search_query = f"{title} {author}"
        try:
            # Search for the video on YouTube
            request = youtube.search().list(
                q=search_query,
                part='snippet',
                type='video',
                order='relevance',
                maxResults=1
            )
            response = request.execute()
            
            if response['items']:
                video_id = response['items'][0]['id']['videoId']
                video_url = f'https://www.youtube.com/watch?v={video_id}'
                print(f"Found video: {video_url}")
                
                # Define the file path
                file_path = os.path.join(download_folder, f"{title}.mp4")
                
                if os.path.exists(file_path):
                    print(f"Video for title '{title}' already exists. Skipping download.")
                    continue

                # Download the video
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': file_path,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    print(f"Downloading {title}...")
                    ydl.download([video_url])
                    print(f"Downloaded {title}")
            else:
                print(f"No video found for title: {title}")
        except Exception as e:
            logging.error(f"An error occurred for {title}: {e}")

# Call the functions
titles_and_authors = insert_songs_and_export_csv(tracks)
search_and_download_youtube_videos(titles_and_authors)
