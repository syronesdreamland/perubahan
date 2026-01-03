import yt_dlp
import os

def download_background_videos():
    # Create assets folder if it doesn't exist
    output_folder = "videos/backgrounds"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List of "Safe" Background Videos (Add more as you find them)
    # These are direct links to specific royalty-free gameplay videos
    video_urls = [
        "https://www.youtube.com/watch?v=n_Dv4JMiwK8",  # Minecraft Parkour (Example)
        "https://www.youtube.com/watch?v=1Y36T2-eCp8",  # GTA 5 Ramp (Example)
        "https://www.youtube.com/watch?v=QPW3XwBoQlw",  # Subway Surfers (Example)
        "https://www.youtube.com/watch?v=369-9t6d9v0",  # Hydraulic Press
    ]

    ydl_opts = {
        'format': 'bestvideo[ext=mp4][height>=1080]/bestvideo[ext=mp4]',  # Download best video only (no audio needed)
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s', # Save to assets folder
        'restrictfilenames': True, # ASCII only filenames
        'match_filter': yt_dlp.utils.match_filter_func("!is_live"),
        'ignoreerrors': True,
    }

    print(f"⬇️  Starting download of {len(video_urls)} background videos...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(video_urls)

    print(f"✅ Downloads complete! Check your '{output_folder}' folder.")

if __name__ == "__main__":
    download_background_videos()
