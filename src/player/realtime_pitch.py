"""Real-time Pitch Detection для микрофона."""

from typing import Optional
import numpy as np

from ..config import (
    SAMPLE_RATE,
    CREPE_CONFIDENCE_THRESHOLD,
    PITCH_MIN_HZ,
    PITCH_MAX_HZ,
)


class RealtimePitchDetector:
    """Определение pitch в реальном времени."""
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu and self._has_gpu()
        self.model = None
        self.last_pitch_hz: float = 0.0
    
    def _has_gpu(self) -> bool:
        """Проверить наличие GPU."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Загрузить модель CREPE."""
        if self.model is None:
            import torchcrepe
            from torchcrepe.model import CREPE
            self.model = CREPE()
            self.model.load(model_capacity="full" if self.use_gpu else "tiny")
    
    def detect(self, audio_block: np.ndarray) -> float:
        """
        Определить pitch для аудио-блока.
        
        Args:
            audio_block: Аудио-блок (1600 сэмплов = 100 мс)
        
        Returns:
            Частота в Гц или 0 (тишина)
        """
        # Если блок слишком короткий или тишина
        if len(audio_block) < 100 or np.max(np.abs(audio_block)) < 0.001:
            self.last_pitch_hz = 0.0
            return 0.0
        
        try:
            # Используем CREPE если доступен, иначе PYIN
            if self.use_gpu and self.model:
                pitch, confidence = self._detect_crepe(audio_block)
            else:
                pitch, confidence = self._detect_pyin(audio_block)
            
            # Проверяем confidence
            if confidence < CREPE_CONFIDENCE_THRESHOLD:
                self.last_pitch_hz = 0.0
                return 0.0
            
            # Ограничиваем диапазон
            if pitch < PITCH_MIN_HZ or pitch > PITCH_MAX_HZ:
                self.last_pitch_hz = 0.0
                return 0.0
            
            self.last_pitch_hz = pitch
            return pitch
            
        except Exception as e:
            # Fallback на 0 при ошибке
            self.last_pitch_hz = 0.0
            return 0.0
    
    def _detect_crepe(self, audio_block: np.ndarray) -> tuple:
        """Определить pitch через CREPE."""
        import torchcrepe
        
        f0, confidence = torchcrepe.predict(
            audio_block,
            sr=SAMPLE_RATE,
            viterbi=False,
            step_size=10,
            model_capacity="full" if self.use_gpu else "tiny",
            device="cuda" if self.use_gpu else "cpu",
            return_periodicity=True
        )
        
        # Берём медиану ненулевых частот
        non_zero = f0[f0 != 0]
        if len(non_zero) == 0:
            return 0.0, 0.0
        
        median_pitch = float(np.median(non_zero))
        median_confidence = float(np.median(confidence))
        
        return median_pitch, median_confidence
    
    def _detect_pyin(self, audio_block: np.ndarray) -> tuple:
        """Определить pitch через PYIN (быстрее на CPU)."""
        import librosa
        
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio_block,
            sr=SAMPLE_RATE,
            fmin=PITCH_MIN_HZ,
            fmax=PITCH_MAX_HZ,
            frame_length=2048,
            hop_length=512
        )
        
        # Берём медиану ненулевых частот
        non_zero = f0[voiced_flag & (f0 != 0)]
        if len(non_zero) == 0:
            return 0.0, 0.0
        
        median_pitch = float(np.median(non_zero))
        median_confidence = float(np.mean(voiced_probs[voiced_flag]))
        
        return median_pitch, median_confidence
    
    def get_last_pitch(self) -> float:
        """Получить последнее измеренное значение pitch."""
        return self.last_pitch_hz
