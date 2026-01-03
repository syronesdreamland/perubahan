import os
import random
import yt_dlp
import subprocess
import json

def getYoutubeVideoLink(url):
    format_filter = "[height<=1920]" if 'shorts' in url else "[height<=1080]"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        # Look for m3u8 formats first, then fall back to regular formats
        "format": f"bestvideo[ext=m3u8]{format_filter}/bestvideo{format_filter}"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(
                url,
                download=False)
            return dictMeta['url'], dictMeta['duration']
    except Exception as e:
        raise Exception(f"Failed getting video link from the following video/url {url} {e.args[0]}")

def extract_random_clip_from_video(video_url, video_duration, clip_duration, output_file):
    """Extracts a clip from a video using a signed URL.
    Args:
        video_url (str): The signed URL of the video.
        video_url (int): Duration of the video.
        start_time (int): The start time of the clip in seconds.
        clip_duration (int): The duration of the clip in seconds.
        output_file (str): The output file path for the extracted clip.
    """
    if not video_duration:
        raise Exception("Could not get video duration")
    
    # If video is shorter than needed clip, loop it or just take what we can
    if video_duration < clip_duration:
        print(f"Warning: Video duration ({video_duration}) is shorter than clip duration ({clip_duration}). Looping/extending.")
        # For now, just start from 0
        start_time = 0
    else:
        # Ensure we don't go out of bounds
        max_start = video_duration - clip_duration
        if max_start <= 0:
            start_time = 0
        else:
            # Try to avoid the very beginning and end if possible
            safe_start = video_duration * 0.15
            safe_end = video_duration * 0.85
            if safe_end - safe_start > clip_duration:
                start_time = safe_start + random.random() * (safe_end - safe_start - clip_duration)
            else:
                start_time = random.random() * max_start

    # If local file, use it directly. If URL, use it.
    input_arg = video_url
    
    # If we need to loop (video shorter than clip), we need a complex filter or just loop input
    # Simple approach: if video is short, just use stream_loop
    
    command = ['ffmpeg', '-y', '-loglevel', 'error']
    
    if video_duration < clip_duration:
        command.extend(['-stream_loop', '-1'])
        
    command.extend([
        '-ss', str(start_time),
        '-t', str(clip_duration),
        '-i', input_arg,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-y',
        output_file
    ])
    
    print(f"Extracting clip: {' '.join(command)}")
    subprocess.run(command, check=True)
    
    if not os.path.exists(output_file):
        raise Exception("Random clip failed to be written")
    
    # Verify file size
    if os.path.getsize(output_file) < 1000:
        raise Exception(f"Random clip file is too small ({os.path.getsize(output_file)} bytes), likely corrupted.")
        
    return output_file


def get_aspect_ratio(video_file):
    cmd = 'ffprobe -i "{}" -v quiet -print_format json -show_format -show_streams'.format(video_file)
#     jsonstr = subprocess.getoutput(cmd)
    jsonstr = subprocess.check_output(cmd, shell=True, encoding='utf-8')
    r = json.loads(jsonstr)
    # look for "codec_type": "video". take the 1st one if there are mulitple
    video_stream_info = [x for x in r['streams'] if x['codec_type']=='video'][0]
    if 'display_aspect_ratio' in video_stream_info and video_stream_info['display_aspect_ratio']!="0:1":
        a,b = video_stream_info['display_aspect_ratio'].split(':')
        dar = int(a)/int(b)
    else:
        # some video do not have the info of 'display_aspect_ratio'
        w,h = video_stream_info['width'], video_stream_info['height']
        dar = int(w)/int(h)
        ## not sure if we should use this
        #cw,ch = video_stream_info['coded_width'], video_stream_info['coded_height']
        #sar = int(cw)/int(ch)
    if 'sample_aspect_ratio' in video_stream_info and video_stream_info['sample_aspect_ratio']!="0:1":
        # some video do not have the info of 'sample_aspect_ratio'
        a,b = video_stream_info['sample_aspect_ratio'].split(':')
        sar = int(a)/int(b)
    else:
        sar = dar
    par = dar/sar
    return dar