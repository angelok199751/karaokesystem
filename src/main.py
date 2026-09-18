"""Точка входа приложения KaraokeForge."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .ui.main_window import MainWindow
from .utils.paths import ensure_dirs
from .utils.models import check_all_models, get_missing_models


def main():
    """Запуск приложения."""
    # Инициализация путей
    ensure_dirs()
    
    # Создаём приложение
    app = QApplication(sys.argv)
    app.setApplicationName("KaraokeForge")
    app.setOrganizationName("KaraokeForge")
    
    # Настраиваем шрифт
    font = QFont("Segoe UI", 12)
    if not font.exactMatch():
        font = QFont("Ubuntu", 12)
        if not font.exactMatch():
            font = QFont("SF Pro", 12)
    app.setFont(font)
    
    # Проверяем модели
    if not check_all_models():
        missing = get_missing_models()
        print(f"Отсутствуют модели: {missing}")
        # В полной версии здесь будет диалог загрузки
    
    # Создаём главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
