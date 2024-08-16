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
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup

# Set up logging
logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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

    for item in tracks:  # Process all songs
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

# Fetch playlist tracks with pagination
def fetch_spotify_tracks(sp_playlist_id, headers):
    tracks = []
    url = f'https://api.spotify.com/v1/playlists/{sp_playlist_id}/tracks'
    
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        tracks.extend(data.get('items', []))
        url = data.get('next')  # Spotify provides the next page URL, if available

    return tracks

# Search YouTube for the given titles and download the videos
def search_and_download_youtube_videos(titles_and_authors, youtube_api_key, num_videos, download_folder='videos'):
    youtube = build('youtube', 'v3', developerKey=youtube_api_key)
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    for title, author in titles_and_authors[:num_videos]:  # Limit to num_videos
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

# Kivy Application
class MusicApp(App):
    def build(self):
        self.title = 'Music Playlist Processor'
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Input fields
        self.sp_playlist_id = TextInput(hint_text='Spotify Playlist ID')
        self.sp_client_id = TextInput(hint_text='Spotify Client ID')
        self.sp_client_secret = TextInput(hint_text='Spotify Client Secret')
        self.yt_api_key = TextInput(hint_text='YouTube API Key')
        self.num_videos_slider = Slider(min=1, max=10, value=5, step=1)
        self.num_videos_label = Label(text=f'Number of videos to download: {int(self.num_videos_slider.value)}')
        
        self.num_videos_slider.bind(value=self.update_video_label)

        process_button = Button(text='Process Playlist')
        process_button.bind(on_press=self.process_data)
        
        layout.add_widget(self.sp_playlist_id)
        layout.add_widget(self.sp_client_id)
        layout.add_widget(self.sp_client_secret)
        layout.add_widget(self.yt_api_key)
        layout.add_widget(self.num_videos_label)
        layout.add_widget(self.num_videos_slider)
        layout.add_widget(process_button)
        
        return layout

    def update_video_label(self, instance, value):
        self.num_videos_label.text = f'Number of videos to download: {int(value)}'

    def process_data(self, instance):
        sp_playlist_id = self.sp_playlist_id.text
        sp_client_id = self.sp_client_id.text
        sp_client_secret = self.sp_client_secret.text
        youtube_api_key = self.yt_api_key.text
        num_videos = int(self.num_videos_slider.value)

        if not sp_playlist_id or not sp_client_id or not sp_client_secret or not youtube_api_key:
            self.show_popup('Error', 'Please fill in all fields')
            return

        # Encode credentials
        encoded_credentials = base64.b64encode(f'{sp_client_id}:{sp_client_secret}'.encode()).decode()

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

        if not access_token:
            self.show_popup('Error', 'Failed to retrieve Spotify access token')
            return

        # Fetch playlist tracks with pagination
        headers = {'Authorization': f'Bearer {access_token}'}
        tracks = fetch_spotify_tracks(sp_playlist_id, headers)

        if not tracks:
            self.show_popup('Error', 'No tracks found or error fetching playlist')
            return

        titles_and_authors = insert_songs_and_export_csv(tracks)
        search_and_download_youtube_videos(titles_and_authors, youtube_api_key, num_videos=num_videos)

        self.show_popup('Success', 'Data processed and videos downloaded successfully!')

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.open()

if __name__ == '__main__':
    MusicApp().run()
