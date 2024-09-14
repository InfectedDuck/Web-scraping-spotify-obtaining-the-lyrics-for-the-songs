# Web-scraping-spotify-obtaining-the-lyrics-for-the-songs
## Spotify Playlist Scraper and YouTube Video Downloader

This project is a full-stack Python application designed to scrape songs from Spotify playlists and download their corresponding music videos from YouTube. It leverages a range of technologies including **Spotify API**, **YouTube Data API**, **Django** for testing, **SQLAlchemy** for database management, and **Kivy** for a user-friendly graphical interface.

### Key Features:
- **Spotify Playlist Scraping**: Using Spotify’s API, the application fetches song metadata (title, artist, added date) from any user-provided Spotify playlist. It handles pagination for large playlists and stores song data in an **SQLite** database using SQLAlchemy ORM.
  
- **CSV Export**: Extracted songs are exported to a CSV file with fields such as song title, artist, and added date for easy accessibility and future reference.

- **YouTube Video Search and Download**: The application integrates with the YouTube Data API to search for music videos related to the songs scraped from Spotify. After identifying the relevant video, it uses **yt-dlp** to download the videos, ensuring the highest quality available.
  
- **Kivy GUI**: The project features a responsive, easy-to-use graphical user interface (GUI) built with Kivy. Users can input their Spotify playlist ID, YouTube API key, and the number of videos to download through the app’s interactive interface.

- **Error Handling & Logging**: To ensure smooth execution, the application includes robust error handling mechanisms, and any exceptions are logged for future debugging.

This project demonstrates my expertise in API integration, data management, and building user-friendly applications with **Python**. By utilizing industry-standard libraries like **SQLAlchemy**, **yt-dlp**, and **Kivy**, this project showcases my ability to work on end-to-end solutions combining backend data processing and frontend design.

Downloads last videos only
## Currently working on this project

## Future Work
The next step involves implementing functionality to search for song lyrics based on the song name. However, a key challenge is identifying a comprehensive source for lyrics. Some websites lack lyrics for Japanese songs, while others may not include English songs, making it difficult to find a single platform that provides lyrics for all languages and genres.

