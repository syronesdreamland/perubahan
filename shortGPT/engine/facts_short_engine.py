from shortGPT.audio.voice_module import VoiceModule
from shortGPT.gpt import facts_gpt
from shortGPT.config.languages import Language
from shortGPT.engine.content_short_engine import ContentShortEngine
from shortGPT.database.content_history_db import ContentHistoryDatabase
from shortGPT.editing_framework.editing_engine import EditingEngine, EditingStep
import os


class FactsShortEngine(ContentShortEngine):

    def __init__(self, voiceModule: VoiceModule, facts_type: str, background_video_name: str, background_music_name: str,short_id="",
                 num_images=None, watermark=None, language:Language = Language.ENGLISH):
        super().__init__(short_id=short_id, short_type="facts_shorts", background_video_name=background_video_name, background_music_name=background_music_name,
                 num_images=num_images, watermark=watermark, language=language, voiceModule=voiceModule)
        
        self._db_facts_type = facts_type
        self.history_db = ContentHistoryDatabase()

    def _generateScript(self):
        """
        Implements Abstract parent method to generate the script for the Facts short.
        """
        # Handle Custom Topic logic
        prompt_type = self._db_facts_type

        recent_facts = self.history_db.get_recent_facts(limit=15)
        self._db_script = facts_gpt.generateFacts(prompt_type, previously_used=recent_facts)
        self.history_db.add_fact(self._db_script)

    def _editAndRenderShort(self):
        """
        Override to add specific visual effects for new modes
        """
        import os # Ensure os is available
        super()._editAndRenderShort() # This runs the standard pipeline. 
        # Wait, standard pipeline renders the video immediately. We need to intercept or modify the schema BEFORE rendering.
        # The standard _editAndRenderShort in ContentShortEngine does everything.
        # We should override it completely or modify the schema generation.
        # Actually, ContentShortEngine._editAndRenderShort builds the EditingEngine and calls renderVideo.
        # We need to copy-paste and modify, or use a hook if available. No hook available.
        # Let's copy-paste the logic from ContentShortEngine and add our effects.
        
        self.verifyParameters(
            voiceover_audio_url=self._db_audio_path,
            video_duration=self._db_background_video_duration,
            music_url=self._db_background_music_url)

        outputPath = self.dynamicAssetDir+"rendered_video.mp4"
        if not (os.path.exists(outputPath)):
            self.logger("Rendering short: Starting automated editing...")
            videoEditor = EditingEngine()
            videoEditor.addEditingStep(EditingStep.ADD_VOICEOVER_AUDIO, {
                                       'url': self._db_audio_path})
            videoEditor.addEditingStep(EditingStep.ADD_BACKGROUND_MUSIC, {'url': self._db_background_music_url,
                                                                          'loop_background_music': self._db_voiceover_duration,
                                                                          "volume_percentage": 0.11})
            
            # Custom Effects Logic
            bg_actions = []
            
            if "Weird Laws" in self._db_facts_type:
                bg_actions.append({'type': 'police_lights', 'param': None})
            elif "Dark History" in self._db_facts_type:
                bg_actions.append({'type': 'black_and_white', 'param': None})

            videoEditor.addEditingStep(EditingStep.CROP_1920x1080, {
                                       'url': self._db_background_trimmed,
                                       'actions': bg_actions
                                       })
            
            videoEditor.addEditingStep(EditingStep.ADD_SUBSCRIBE_ANIMATION, {'url': AssetDatabase.get_asset_link('subscribe animation')})

            if self._db_watermark:
                videoEditor.addEditingStep(EditingStep.ADD_WATERMARK, {
                                           'text': self._db_watermark})

            caption_type = EditingStep.ADD_CAPTION_SHORT_ARABIC if self._db_language == Language.ARABIC.value else EditingStep.ADD_CAPTION_SHORT
            for timing, text in self._db_timed_captions:
                videoEditor.addEditingStep(caption_type, {'text': text.upper(),
                                                          'set_time_start': timing[0],
                                                          'set_time_end': timing[1]})
            if self._db_num_images:
                for timing, image_url in self._db_timed_image_urls:
                    videoEditor.addEditingStep(EditingStep.SHOW_IMAGE, {'url': image_url,
                                                                        'set_time_start': timing[0],
                                                                        'set_time_end': timing[1]})
            videoEditor.renderVideo(outputPath, logger= self.logger if self.logger is not self.default_logger else None)

        self._db_video_path = outputPath

