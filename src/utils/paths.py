"""Управление путями к данным, моделям и кэшу."""

from pathlib import Path


def get_base_dir() -> Path:
    """Базовая директория приложения."""
    return Path.home() / ".karaoke-forge"


def get_models_dir() -> Path:
    """Директория для ML-моделей."""
    return get_base_dir() / "models"


def get_output_dir() -> Path:
    """Директория для выходных файлов."""
    return get_base_dir() / "output"


def get_cache_dir() -> Path:
    """Директория для кэша."""
    return get_base_dir() / "cache"


def ensure_dirs() -> None:
    """Создать все необходимые директории."""
    get_models_dir().mkdir(parents=True, exist_ok=True)
    get_output_dir().mkdir(parents=True, exist_ok=True)
    get_cache_dir().mkdir(parents=True, exist_ok=True)
