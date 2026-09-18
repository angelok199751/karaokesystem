"""Загрузка и кэширование ML-моделей."""

import os
from pathlib import Path
from typing import Dict, List

from .paths import get_models_dir


MODELS_INFO: Dict[str, Dict] = {
    "demucs": {
        "name": "htdemucs",
        "size_gb": 0.08,
        "repo": "facebookresearch/demucs",
    },
    "whisper": {
        "name": "large-v3",
        "size_gb": 3.0,
        "repo": "openai/whisper",
    },
    "wav2vec2": {
        "name": "wav2vec2-large-xlsr-53-russian",
        "size_gb": 1.3,
        "repo": "jonatasgrosman/wav2vec2-large-xlsr-53-russian",
    },
}


def check_model(model_type: str) -> bool:
    """Проверить наличие модели."""
    models_dir = get_models_dir()
    model_info = MODELS_INFO.get(model_type)
    if not model_info:
        return False
    
    model_path = models_dir / model_type / model_info["name"]
    return model_path.exists()


def check_all_models() -> bool:
    """Проверить наличие всех моделей."""
    return all(check_model(m) for m in MODELS_INFO.keys())


def get_missing_models() -> List[str]:
    """Вернуть список отсутствующих моделей."""
    return [m for m in MODELS_INFO.keys() if not check_model(m)]


def download_model(model_type: str, progress_callback=None) -> None:
    """
    Скачать модель.
    
    Args:
        model_type: Тип модели (demucs, whisper, wav2vec2)
        progress_callback: Callback для обновления прогресса (0.0-1.0)
    """
    import torch
    from .paths import get_models_dir
    
    models_dir = get_models_dir()
    
    if model_type == "demucs":
        # Demucs загружается автоматически при первом использовании
        # Просто убедимся, что директория существует
        (models_dir / "demucs").mkdir(parents=True, exist_ok=True)
        if progress_callback:
            progress_callback(1.0)
    
    elif model_type == "whisper":
        # Whisper large-v3 через faster-whisper
        from faster_whisper import WhisperModel
        
        model_path = models_dir / "whisper" / "large-v3"
        if not model_path.exists():
            # Загружаем модель - она закэшируется в ~/.cache/huggingface
            _ = WhisperModel("large-v3", device="cpu", compute_type="int8")
            (models_dir / "whisper").mkdir(parents=True, exist_ok=True)
            # Создаём маркер загрузки
            (model_path / ".loaded").touch()
        
        if progress_callback:
            progress_callback(1.0)
    
    elif model_type == "wav2vec2":
        # Wav2Vec2 для alignment
        from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
        
        model_name = "jonatasgrosman/wav2vec2-large-xlsr-53-russian"
        model_path = models_dir / "wav2vec2" / "wav2vec2-large-xlsr-53-russian"
        
        if not model_path.exists():
            # Загружаем модель - она закэшируется в ~/.cache/huggingface
            _ = Wav2Vec2Processor.from_pretrained(model_name)
            _ = Wav2Vec2ForCTC.from_pretrained(model_name)
            (models_dir / "wav2vec2").mkdir(parents=True, exist_ok=True)
            (model_path / ".loaded").touch()
        
        if progress_callback:
            progress_callback(1.0)


def download_all(progress_callback=None) -> None:
    """
    Скачать все модели.
    
    Args:
        progress_callback: Callback(total_models, current_model, model_progress)
    """
    missing = get_missing_models()
    total = len(missing)
    
    for i, model_type in enumerate(missing):
        def model_progress(p):
            if progress_callback:
                progress_callback(total, i + 1, p)
        
        download_model(model_type, model_progress)
