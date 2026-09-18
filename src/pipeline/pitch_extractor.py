"""Извлечение Pitch Contour с помощью CREPE."""

from typing import Tuple

import numpy as np

from ..config import (
    SAMPLE_RATE,
    CREPE_MODEL_CAPACITY,
    CREPE_STEP_SIZE_MS,
    CREPE_CONFIDENCE_THRESHOLD,
    PITCH_MIN_HZ,
    PITCH_MAX_HZ,
)


class PitchExtractor:
    """Извлечение pitch contour из вокала."""
    
    def __init__(self):
        self.model = None
    
    def _load_model(self):
        """Загрузить модель CREPE."""
        if self.model is None:
            import crepe
            self.model = crepe.model.CREPE()
            self.model.load(model_capacity=CREPE_MODEL_CAPACITY)
    
    def extract(
        self,
        vocals_path: str,
        progress_callback=None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Извлечь pitch contour.
        
        Args:
            vocals_path: Путь к вокалу
            progress_callback: Callback для обновления прогресса
        
        Returns:
            (frequencies_hz, confidence) - массивы с шагом CREPE_STEP_SIZE_MS
        """
        import crepe
        import librosa
        
        # Загружаем аудио
        audio, sr = librosa.load(vocals_path, sr=SAMPLE_RATE)
        
        if progress_callback:
            progress_callback(0.1)
        
        # Предсказываем pitch
        f0, confidence = crepe.predict(
            audio,
            sr=SAMPLE_RATE,
            viterbi=True,
            step_size=CREPE_STEP_SIZE_MS,
            model_capacity=CREPE_MODEL_CAPACITY,
            device="cuda" if hasattr(__import__('torch'), 'cuda') and __import__('torch').cuda.is_available() else "cpu"
        )
        
        if progress_callback:
            progress_callback(0.9)
        
        # Обнуляем частоты с низким confidence
        frequencies = f0.copy()
        frequencies[confidence < CREPE_CONFIDENCE_THRESHOLD] = 0
        
        # Ограничиваем диапазон
        frequencies[(frequencies < PITCH_MIN_HZ) | (frequencies > PITCH_MAX_HZ)] = 0
        
        if progress_callback:
            progress_callback(1.0)
        
        return frequencies, confidence
