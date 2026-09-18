"""Координатор пайплайна генерации караоке."""

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Callable

from ..utils.audio import load_audio, normalize_audio, save_audio
from ..config import NORMALIZE_HEADROOM_DB


class KaraokeOrchestrator:
    """Координатор пайплайна генерации караоке."""
    
    def __init__(self):
        self.separator = None
        self.aligner = None
        self.pitch_extractor = None
        self.cleaner = None
        self.builder = None
    
    def _init_components(self):
        """Инициализировать компоненты пайплайна."""
        if self.separator is None:
            from .separator import VocalSeparator
            self.separator = VocalSeparator()
        
        if self.aligner is None:
            from .aligner import TextAligner
            self.aligner = TextAligner()
        
        if self.pitch_extractor is None:
            from .pitch_extractor import PitchExtractor
            self.pitch_extractor = PitchExtractor()
        
        if self.cleaner is None:
            from .cleaner import PitchCleaner
            self.cleaner = PitchCleaner()
        
        if self.builder is None:
            from .builder import KaraokeBuilder
            self.builder = KaraokeBuilder()
    
    def generate(
        self,
        audio_path: str,
        lyrics_path: Optional[str] = None,
        title: str = "",
        artist: str = "",
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Сгенерировать караоке-файл.
        
        Args:
            audio_path: Путь к аудиофайлу
            lyrics_path: Путь к текстовому файлу (опционально)
            title: Название песни
            artist: Исполнитель
            progress_callback: Callback(progress_percent, status_message)
        
        Returns:
            Путь к karaoke.json
        """
        self._init_components()
        
        # Создаём временную директорию
        temp_dir = tempfile.mkdtemp(prefix="karaoke_forge_")
        
        try:
            # 1. Валидация и нормализация
            if progress_callback:
                progress_callback(5, "Загрузка и нормализация аудио...")
            
            audio, sr = load_audio(audio_path)
            audio = normalize_audio(audio, NORMALIZE_HEADROOM_DB)
            
            normalized_path = Path(temp_dir) / "normalized.wav"
            save_audio(str(normalized_path), audio, sr)
            
            # Загружаем текст если есть
            lyrics_text = None
            if lyrics_path and Path(lyrics_path).exists():
                with open(lyrics_path, "r", encoding="utf-8") as f:
                    lyrics_text = [line.strip() for line in f if line.strip()]
            
            # Если title/artist не указаны, берём из имени файла
            if not title:
                title = Path(audio_path).stem
            if not artist:
                artist = "Unknown"
            
            # 2. Сепарация вокала
            if progress_callback:
                progress_callback(15, "Разделение вокала и музыки...")
            
            vocals_path, instrumental_path = self.separator.separate(
                str(normalized_path),
                lambda p: progress_callback(15 + p * 15, "Разделение вокала и музыки...") if progress_callback else None
            )
            
            # 3. Alignment
            if progress_callback:
                progress_callback(45, "Определение таймингов текста...")
            
            words = self.aligner.align(
                vocals_path,
                lyrics_text,
                lambda p: progress_callback(45 + p * 15, "Определение таймингов текста...") if progress_callback else None
            )
            
            # 4. Извлечение pitch
            if progress_callback:
                progress_callback(70, "Извлечение мелодии...")
            
            frequencies, confidence = self.pitch_extractor.extract(
                vocals_path,
                lambda p: progress_callback(70 + p * 5, "Извлечение мелодии...") if progress_callback else None
            )
            
            # 5. Очистка pitch
            clean_frequencies = self.cleaner.clean(frequencies, confidence)
            
            # 6. Сборка караоке
            if progress_callback:
                progress_callback(85, "Сборка караоке-файла...")
            
            output_dir = Path.home() / ".karaoke-forge" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            karaoke_path = self.builder.build(
                words=words,
                pitch_frequencies=clean_frequencies,
                instrumental_path=instrumental_path,
                output_dir=output_dir,
                title=title,
                artist=artist,
                source_file=audio_path,
                progress_callback=lambda p: progress_callback(85 + p * 15, "Сборка караоке-файла...") if progress_callback else None
            )
            
            if progress_callback:
                progress_callback(100, "Готово!")
            
            return karaoke_path
            
        finally:
            # Очистка временных файлов
            shutil.rmtree(temp_dir, ignore_errors=True)
