from urllib.error import HTTPError
from shortGPT.config.path_utils import get_program_path
import os
from shortGPT.config.path_utils import handle_path
import numpy as np
from typing import Any, Dict, List, Union
from moviepy import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                    TextClip, VideoFileClip, AudioClip)
from moviepy.Clip import Clip
from moviepy import vfx, afx
from shortGPT.editing_framework.rendering_logger import MoviepyProgressLogger
import json

def load_schema(json_path):
    return json.loads(open(json_path, 'r', encoding='utf-8').read())

class CoreEditingEngine:

    def generate_image(self, schema:Dict[str, Any],output_file , logger=None):
        assets = dict(sorted(schema['visual_assets'].items(), key=lambda item: item[1]['z']))
        clips = []

        for asset_key in assets:
            asset = assets[asset_key]
            asset_type = asset['type']
            if asset_type == 'image':
                clip = self.process_image_asset(asset)
            elif asset_type == 'text':
                clip = self.process_text_asset(asset)
                clips.append(clip)
            else:
                raise ValueError(f'Invalid asset type: {asset_type}')
            clips.append(clip)

        image = CompositeVideoClip(clips)
        image.save_frame(output_file)
        return output_file

    def generate_video(self, schema:Dict[str, Any], output_file, logger=None, force_duration=None, threads=None) -> None:
        visual_assets = dict(sorted(schema['visual_assets'].items(), key=lambda item: item[1]['z']))
        audio_assets = dict(sorted(schema['audio_assets'].items(), key=lambda item: item[1]['z']))
        
        visual_clips = []
        for asset_key in visual_assets:
            asset = visual_assets[asset_key]
            asset_type = asset['type']
            if asset_type == 'video':
                clip = self.process_video_asset(asset)
            elif asset_type == 'image':
                # clip = self.process_image_asset(asset)
                try:
                    clip = self.process_image_asset(asset)
                except Exception as e:
                    print(f"Failed to load image {asset['parameters']['url']}. Error : {str(e)}")
                    continue
            elif asset_type == 'text':
                clip = self.process_text_asset(asset)
            else:
                raise ValueError(f'Invalid asset type: {asset_type}')

            visual_clips.append(clip)
        
        audio_clips = []

        for asset_key in audio_assets:
            asset = audio_assets[asset_key]
            asset_type = asset['type']
            if asset_type == "audio":
                audio_clip = self.process_audio_asset(asset)
            else:
                raise ValueError(f"Invalid asset type: {asset_type}")

            audio_clips.append(audio_clip)
        video = CompositeVideoClip(visual_clips)
        if(audio_clips):
            audio = CompositeAudioClip(audio_clips)
            video = video.with_audio(audio)
            video = video.with_duration(audio.duration)
        if force_duration:
            video = video.with_duration(force_duration)
        if logger:
            my_logger = MoviepyProgressLogger(callBackFunction=logger)
            video.write_videofile(output_file, threads=threads,codec='libx264', audio_codec='aac', fps=25, preset='veryfast', logger=my_logger)
        else:
            video.write_videofile(output_file, threads=threads,codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
        return output_file
    
    def generate_audio(self, schema:Dict[str, Any], output_file, logger=None) -> None:
        audio_assets = dict(sorted(schema['audio_assets'].items(), key=lambda item: item[1]['z']))
        audio_clips = []

        for asset_key in audio_assets:
            asset = audio_assets[asset_key]
            asset_type = asset['type']
            if asset_type == "audio":
                audio_clip = self.process_audio_asset(asset)
            else:
                raise ValueError(f"Invalid asset type: {asset_type}")

            audio_clips.append(audio_clip)
        audio = CompositeAudioClip(audio_clips)
        audio.fps = 44100
        if logger:
            my_logger = MoviepyProgressLogger(callBackFunction=logger)
            audio.write_audiofile(output_file, logger=my_logger)
        else:
            audio.write_audiofile(output_file)
        return output_file
    # Process common actions
    def process_common_actions(self,
                                   clip: Union[VideoFileClip, ImageClip, TextClip, AudioFileClip],
                                   actions: List[Dict[str, Any]]) -> Union[VideoFileClip, AudioFileClip, ImageClip, TextClip]:
        for action in actions:
            if action['type'] == 'set_time_start':
                clip = clip.with_start(action['param'])
                continue
   
            if action['type'] == 'set_time_end':
                clip = clip.with_end(action['param'])
                continue
            
            if action['type'] == 'subclip':
                clip = clip.subclipped(**action['param'])
                continue

        return clip

    # Process common visual clip actions
    def process_common_visual_actions(self,
                                   clip: Clip,
                                   actions: List[Dict[str, Any]]) -> Union[VideoFileClip, ImageClip, TextClip]:
        clip = self.process_common_actions(clip, actions)
        for action in actions:
 
            if action['type'] == 'resize':
                params = action['param']
                if isinstance(params, dict):
                    # Ensure dimensions are > 0
                    params = {k: max(1, int(v)) if isinstance(v, (int, float)) else v for k, v in params.items()}
                    clip = clip.with_effects([vfx.Resize(**params)])
                else:
                    clip = clip.with_effects([vfx.Resize(params)])
                continue

            if action['type'] == 'crop':
                params = action['param']
                params = {k: int(v) if isinstance(v, (int, float)) else v for k, v in params.items()}
                # Validate crop dimensions
                if 'width' in params and params['width'] <= 0: params['width'] = 1
                if 'height' in params and params['height'] <= 0: params['height'] = 1
                clip = clip.with_effects([vfx.Crop(**params)])
                continue

            if action['type'] == 'screen_position':
                clip = clip.with_position(**action['param'])
                continue

            if action['type'] == 'green_screen':
                params = action['param']
                color = params['color'] if  params['color'] else [52, 255, 20]
                thr = params["threshold"] if params["threshold"] else 100
                s = params['stiffness'] if params['stiffness'] else 5
                clip = clip.with_effects([vfx.MaskColor(color=color,threshold=thr, stiffness=s)])
                continue

            if action['type'] == 'normalize_image':
                clip = clip.image_transform(self.__normalize_frame)
                continue

            if action['type'] == 'auto_resize_image':
                ar = clip.aspect_ratio
                height = action['param']['maxHeight']
                width = action['param']['maxWidth']
                if ar <1:
                    clip = clip.with_effects([vfx.Resize((int(height*ar), int(height)))])
                else:
                    clip = clip.with_effects([vfx.Resize((int(width), int(width/ar)))])
                continue

            if action['type'] == 'vhs_glitch':
                # Simple chromatic aberration effect
                def chromatic_aberration(frame):
                    # Shift red channel left, blue channel right
                    shift = 4
                    r = np.roll(frame[:,:,0], shift, axis=1)
                    g = frame[:,:,1]
                    b = np.roll(frame[:,:,2], -shift, axis=1)
                    return np.stack((r,g,b), axis=2)
                
                clip = clip.image_transform(chromatic_aberration)
                continue

            if action['type'] == 'black_and_white':
                clip = clip.with_effects([vfx.BlackAndWhite()])
                continue

            if action['type'] == 'police_lights':
                # Flashing red and blue overlay
                def police_flash(get_frame, t):
                    frame = get_frame(t)
                    # Flash every 0.5 seconds
                    if int(t * 4) % 2 == 0:
                        # Red tint
                        frame[:,:,0] = np.minimum(frame[:,:,0] * 1.5, 255)
                    else:
                        # Blue tint
                        frame[:,:,2] = np.minimum(frame[:,:,2] * 1.5, 255)
                    return frame
                
                clip = clip.fl(police_flash)
                continue

        return clip

    # Process audio actions
    def process_audio_actions(self, clip: AudioClip,
                            actions: List[Dict[str, Any]]) -> AudioClip:
        clip = self.process_common_actions(clip, actions)
        for action in actions:
            if action['type'] == 'normalize_music':
                clip = clip.with_effects([afx.AudioNormalize()])
                continue

            if action['type'] == 'loop_background_music':
                target_duration = action['param']
                start = clip.duration * 0.15
                clip = clip.subclipped(start)
                clip = clip.with_effects([afx.AudioLoop(duration=target_duration)])
                continue

            if action['type'] == 'volume_percentage':
                clip = clip.with_effects([afx.MultiplyVolume(action['param'])])
                continue

        return clip
    # Process individual asset types
    def process_video_asset(self, asset: Dict[str, Any]) -> VideoFileClip:
        params = {
            'filename': handle_path(asset['parameters']['url'])
        }
        if 'audio' in asset['parameters']:
            params['audio'] = asset['parameters']['audio']
        clip = VideoFileClip(**params)
        return self.process_common_visual_actions(clip, asset['actions'])

    def process_image_asset(self, asset: Dict[str, Any]) -> ImageClip:
        clip = ImageClip(asset['parameters']['url'])
        # Optimization: Resize huge images immediately to save memory
        w, h = clip.size
        if w * h > 1920 * 1920:
            from PIL import Image
            print(f"Resizing large image {asset['parameters']['url']} from {w}x{h}")
            img = Image.fromarray(clip.get_frame(0))
            img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            clip = ImageClip(np.array(img))

        return self.process_common_visual_actions(clip, asset['actions'])

    def process_text_asset(self, asset: Dict[str, Any]) -> TextClip:
        text_clip_params = asset['parameters']
        
        if not (any(key in text_clip_params for key in ['text','fontsize', 'size'])):
            raise Exception('You must include at least a size or a fontsize to determine the size of your text')
        text_method = text_clip_params.get('method', 'label')
        clip_info = {
            'text': text_clip_params['text'],
            'font': text_clip_params.get('font'),
            'font_size': text_clip_params.get('font_size'),
            'color': text_clip_params.get('color'),
            'stroke_width': text_clip_params.get('stroke_width'),
            'stroke_color': text_clip_params.get('stroke_color'),
            'size': text_clip_params.get('size'),
            'method': text_method,
            'text_align': text_clip_params.get('text_align', 'center')
        }
        clip_info = {k: v for k, v in clip_info.items() if v is not None}
        clip = TextClip(**clip_info)
        return self.process_common_visual_actions(clip, asset['actions'])

    def process_audio_asset(self, asset: Dict[str, Any]) -> AudioFileClip:
        clip = AudioFileClip(asset['parameters']['url'])
        return self.process_audio_actions(clip, asset['actions'])
    
    def __normalize_image(self, clip):
        def f(get_frame, t):
            if f.normalized_frame is not None:
                return f.normalized_frame
            else:
                frame = get_frame(t)
                f.normalized_frame = self.__normalize_frame(frame)
                return f.normalized_frame

        f.normalized_frame = None

        return clip.fl(f)


    def __normalize_frame(self, frame):
        if frame.ndim == 2:
            return np.stack((frame,)*3, axis=-1)
        return frame
        

