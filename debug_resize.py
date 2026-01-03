from moviepy import VideoFileClip, vfx
import os

video_path = "public/black_background.mp4"
if not os.path.exists(video_path):
    print(f"File not found: {video_path}")
    exit(1)

clip = VideoFileClip(video_path)
print(f"Original size: {clip.size}")

# Simulate the crop
crop_params = {
    "x1": 420,
    "y1": 0,
    "width": 1080,
    "height": 1080
}
clip = clip.with_effects([vfx.Crop(**crop_params)])
print(f"After crop size: {clip.size}")

# Simulate the resize
resize_params = {
    "width": 1920,
    "height": 1920
}
clip = clip.with_effects([vfx.Resize(**resize_params)])
print(f"After resize size: {clip.size}")

# Try to render a frame
try:
    frame = clip.get_frame(0)
    print(f"Frame shape: {frame.shape}")
except Exception as e:
    print(f"Error rendering frame: {e}")
