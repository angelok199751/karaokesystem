"""Аудио-утилиты: нормализация, ресемплинг, конвертация."""

import tempfile
from pathlib import Path
from typing import Tuple

import librosa
import numpy as np
import soundfile as sf

from ..config import SAMPLE_RATE, NORMALIZE_HEADROOM_DB


def load_audio(path: str, target_sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    """
    Загрузить аудиофайл.
    
    Args:
        path: Путь к файлу
        target_sr: Целевая частота дискретизации
    
    Returns:
        (audio_data, sample_rate)
    """
    audio, sr = librosa.load(path, sr=target_sr, mono=True)
    return audio, sr


def save_audio(path: str, audio: np.ndarray, sr: int = SAMPLE_RATE) -> None:
    """
    Сохранить аудиофайл.
    
    Args:
        path: Путь для сохранения
        audio: Аудиоданные
        sr: Частота дискретизации
    """
    sf.write(path, audio, sr)


def normalize_audio(audio: np.ndarray, headroom_db: float = NORMALIZE_HEADROOM_DB) -> np.ndarray:
    """
    Нормализовать аудио с заданным headroom.
    
    Args:
        audio: Аудиоданные
        headroom_db: Запас в дБ (отрицательное значение)
    
    Returns:
        Нормализованные аудиоданные
    """
    peak = np.max(np.abs(audio))
    if peak == 0:
        return audio
    
    # Конвертируем dB в линейный коэффициент
    target_peak = 10 ** (headroom_db / 20)
    scale = target_peak / peak
    
    return audio * scale


def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Ресемплировать аудио.
    
    Args:
        audio: Аудиоданные
        orig_sr: Исходная частота дискретизации
        target_sr: Целевая частота дискретизации
    
    Returns:
        Ресемплированные аудиоданные
    """
    if orig_sr == target_sr:
        return audio
    
    return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)


def convert_to_wav(input_path: str, output_path: str = None) -> str:
    """
    Конвертировать аудиофайл в WAV.
    
    Args:
        input_path: Путь к входному файлу
        output_path: Путь для выходного файла (если None, создаётся временный)
    
    Returns:
        Путь к WAV-файлу
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.wav')
        import os
        os.close(fd)
    
    audio, sr = load_audio(input_path)
    save_audio(output_path, audio, sr)
    
    return output_path


def get_duration(path: str) -> float:
    """
    Получить длительность аудиофайла в секундах.
    
    Args:
        path: Путь к файлу
    
    Returns:
        Длительность в секундах
    """
    audio, sr = load_audio(path)
    return len(audio) / sr
