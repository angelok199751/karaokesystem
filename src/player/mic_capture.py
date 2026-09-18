"""Захват микрофона в реальном времени."""

import numpy as np
from typing import Optional, Callable

import sounddevice as sd

from ..config import SAMPLE_RATE, NOISE_GATE_RMS


class MicCapture:
    """Захват аудио с микрофона."""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.block_size = int(sample_rate * 0.1)  # 100 мс буфер
        self.ring_buffer: Optional[np.ndarray] = None
        self.stream: Optional[sd.InputStream] = None
        self.noise_gate_threshold = NOISE_GATE_RMS
    
    def start(self, callback: Callable[[np.ndarray], None]) -> None:
        """
        Начать захват микрофона.
        
        Args:
            callback: Функция для обработки каждого блока аудио
        """
        def stream_callback(indata, frames, time, status):
            if status:
                print(f"Stream status: {status}")
            
            audio_block = indata[:, 0].copy()  # Берём первый канал (моно)
            
            # Применяем noise gate
            rms = np.sqrt(np.mean(audio_block ** 2))
            if rms < self.noise_gate_threshold:
                audio_block[:] = 0
            
            callback(audio_block)
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            blocksize=self.block_size,
            callback=stream_callback
        )
        self.stream.start()
    
    def stop(self) -> None:
        """Остановить захват микрофона."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def set_noise_gate(self, threshold: float) -> None:
        """Установить порог noise gate."""
        self.noise_gate_threshold = threshold
    
    def get_rms(self, audio_block: np.ndarray) -> float:
        """Вычислить RMS амплитуду блока."""
        return float(np.sqrt(np.mean(audio_block ** 2)))
