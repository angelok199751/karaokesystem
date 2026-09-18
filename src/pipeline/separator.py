"""Сепарация вокала с помощью Demucs."""

import tempfile
import shutil
from pathlib import Path
from typing import Tuple

import torch

from ..config import DEMUCS_MODEL, DEMUCS_SHIFTS, DEMUCS_OVERLAP


class VocalSeparator:
    """Сепарация вокала и инструментала."""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def _load_model(self):
        """Загрузить модель Demucs."""
        if self.model is None:
            from demucs.pretrained import get_model
            self.model = get_model(DEMUCS_MODEL)
            self.model.to(self.device)
    
    def separate(self, audio_path: str, progress_callback=None) -> Tuple[str, str]:
        """
        Разделить аудио на вокал и инструментал.
        
        Args:
            audio_path: Путь к входному аудиофайлу
            progress_callback: Callback для обновления прогресса (0.0-1.0)
        
        Returns:
            (путь_к_vocals.wav, путь_к_instrumental.wav)
        """
        self._load_model()
        
        # Создаём временную директорию для результатов
        temp_dir = tempfile.mkdtemp(prefix="demucs_")
        
        try:
            from demucs.apply import apply_model
            from demucs.audio import save_audio
            import torchaudio
            
            # Загружаем аудио
            wav, sr = torchaudio.load(audio_path)
            
            # Конвертируем в стерео если нужно
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)
            
            # Применяем модель
            ref = self.model(wav.to(self.device))
            
            # Получаем результаты
            vocals = ref[0][3].cpu()  # Индекс 3 = vocals в htdemucs
            instrumental = (ref[0][0] + ref[0][1] + ref[0][2]).cpu()  # drums + bass + other
            
            # Сохраняем файлы
            vocals_path = Path(temp_dir) / "vocals.wav"
            instrumental_path = Path(temp_dir) / "instrumental.wav"
            
            save_audio(vocals, vocals_path, samplerate=self.model.samplerate)
            save_audio(instrumental, instrumental_path, samplerate=self.model.samplerate)
            
            if progress_callback:
                progress_callback(1.0)
            
            return str(vocals_path), str(instrumental_path)
            
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Ошибка сепарации: {e}")
