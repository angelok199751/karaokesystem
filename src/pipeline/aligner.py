"""Forced Alignment с помощью WhisperX."""

import tempfile
from pathlib import Path
from typing import List, Dict, Optional

from ..config import WHISPER_MODEL, WHISPER_LANGUAGE, ALIGNMENT_MODEL


class TextAligner:
    """Выравнивание текста по аудио."""
    
    def __init__(self):
        self.whisper_model = None
        self.alignment_model = None
    
    def _load_whisper(self):
        """Загрузить Whisper модель."""
        if self.whisper_model is None:
            from faster_whisper import WhisperModel
            self.whisper_model = WhisperModel(
                WHISPER_MODEL,
                device="cuda",
                compute_type="float16"
            )
    
    def _load_alignment(self):
        """Загрузить модель alignment."""
        if self.alignment_model is None:
            import whisperx
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.alignment_model = whisperx.load_align_model(
                language_code=WHISPER_LANGUAGE,
                device=device,
                model_name=ALIGNMENT_MODEL
            )
    
    def align(
        self,
        vocals_path: str,
        lyrics_text: Optional[List[str]] = None,
        progress_callback=None
    ) -> List[Dict]:
        """
        Выполнить forced alignment.
        
        Args:
            vocals_path: Путь к вокалу
            lyrics_text: Список строк текста (опционально)
            progress_callback: Callback для обновления прогресса
        
        Returns:
            Список слов с таймкодами: [{"text": "...", "start": 0.0, "end": 1.0}, ...]
        """
        import whisperx
        import torch
        
        self._load_whisper()
        
        if progress_callback:
            progress_callback(0.2)
        
        # Транскрипция
        segments, info = self.whisper_model.transcribe(
            vocals_path,
            language=WHISPER_LANGUAGE,
            initial_prompt=" ".join(lyrics_text) if lyrics_text else None,
            word_timestamps=True
        )
        
        words_list = []
        for segment in segments:
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    words_list.append({
                        "text": word.word.strip(),
                        "start": word.start,
                        "end": word.end
                    })
        
        if progress_callback:
            progress_callback(0.8)
        
        # Alignment через whisperx
        device = "cuda" if torch.cuda.is_available() else "cpu"
        audio, sample_rate = whisperx.load_audio(vocals_path)
        
        try:
            model_a, metadata = whisperx.load_align_model(
                language_code=WHISPER_LANGUAGE,
                device=device
            )
            
            aligned_result = whisperx.align(
                words_list,
                model_a,
                metadata,
                audio,
                device,
                return_char_alignments=False
            )
            
            if progress_callback:
                progress_callback(1.0)
            
            # Форматируем результат
            result = []
            for word in aligned_result["word_segments"]:
                result.append({
                    "text": word["word"],
                    "start_sec": float(word["start"]),
                    "end_sec": float(word["end"])
                })
            
            return result
            
        except Exception as e:
            # Fallback: вернуть слова без alignment
            if progress_callback:
                progress_callback(1.0)
            return words_list
