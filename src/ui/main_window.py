"""Главное окно приложения."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QCheckBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QStackedWidget, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QFont

from ..config import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from ..utils.paths import get_output_dir
from ..pipeline.orchestrator import KaraokeOrchestrator


class GeneratorWorker(QThread):
    """Worker для генерации караоке в отдельном потоке."""
    
    progress = Signal(float, str)
    finished = Signal(str)  # путь к karaoke.json
    error = Signal(str)
    
    def __init__(self, audio_path: str, lyrics_path: Optional[str], title: str, artist: str):
        super().__init__()
        self.audio_path = audio_path
        self.lyrics_path = lyrics_path
        self.title = title
        self.artist = artist
    
    def run(self):
        try:
            orchestrator = KaraokeOrchestrator()
            
            def on_progress(percent: float, message: str):
                self.progress.emit(percent, message)
            
            karaoke_path = orchestrator.generate(
                audio_path=self.audio_path,
                lyrics_path=self.lyrics_path,
                title=self.title,
                artist=self.artist,
                progress_callback=on_progress
            )
            
            self.finished.emit(karaoke_path)
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.current_karaoke_file: Optional[str] = None
        self.generator_worker: Optional[GeneratorWorker] = None
        
        self._setup_ui()
        self._load_styles()
        self._populate_song_list()
    
    def _setup_ui(self):
        """Создать пользовательский интерфейс."""
        self.setWindowTitle("KaraokeForge")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        title_label = QLabel("🎤 KaraokeForge")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Экраны
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Экран 1: Главный
        screen1 = self._create_main_screen()
        self.stack.addWidget(screen1)
        
        # Экран 2: Генерация
        screen2 = self._create_generator_screen()
        self.stack.addWidget(screen2)
        
        # Показываем первый экран
        self.stack.setCurrentIndex(0)
    
    def _create_main_screen(self) -> QWidget:
        """Создать главный экран."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Выбор файла
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setStyleSheet("color: #6c7086;")
        
        select_file_btn = QPushButton("Выбрать песню")
        select_file_btn.clicked.connect(self._select_audio_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_file_btn)
        
        layout.addLayout(file_layout)
        
        # Чекбокс текста
        self.has_lyrics_checkbox = QCheckBox("У меня есть текст песни")
        self.has_lyrics_checkbox.stateChanged.connect(self._on_lyrics_checkbox_changed)
        layout.addWidget(self.has_lyrics_checkbox)
        
        # Выбор текста
        self.lyrics_layout = QHBoxLayout()
        self.lyrics_layout.setEnabled(False)
        
        self.lyrics_label = QLabel("Текст не выбран")
        self.lyrics_label.setStyleSheet("color: #6c7086;")
        
        select_lyrics_btn = QPushButton("Выбрать текст")
        select_lyrics_btn.clicked.connect(self._select_lyrics_file)
        
        self.lyrics_layout.addWidget(self.lyrics_label)
        self.lyrics_layout.addWidget(select_lyrics_btn)
        layout.addLayout(self.lyrics_layout)
        
        # Название и исполнитель
        meta_layout = QHBoxLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Название песни")
        
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Исполнитель")
        
        meta_layout.addWidget(self.title_input)
        meta_layout.addWidget(self.artist_input)
        layout.addLayout(meta_layout)
        
        # Кнопка генерации
        generate_btn = QPushButton("Сгенерировать караоке")
        generate_btn.setObjectName("accentButton")
        generate_btn.setMinimumHeight(50)
        generate_btn.clicked.connect(self._start_generation)
        layout.addWidget(generate_btn)
        
        # Разделитель
        from PySide6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #45475a;")
        line.setMaximumHeight(2)
        layout.addWidget(line)
        
        # Открыть готовое
        open_btn = QPushButton("Открыть готовое караоке")
        open_btn.clicked.connect(self._open_karaoke_file)
        layout.addWidget(open_btn)
        
        # Список песен
        songs_label = QLabel("Ранее сгенерированные:")
        layout.addWidget(songs_label)
        
        self.songs_list = QListWidget()
        self.songs_list.itemDoubleClicked.connect(self._on_song_double_clicked)
        layout.addWidget(self.songs_list)
        
        return widget
    
    def _create_generator_screen(self) -> QWidget:
        """Создать экран генерации."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Заголовок
        title = QLabel("Генерация караоке...")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimumHeight(20)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("Загрузка...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Кнопка отмены
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self._cancel_generation)
        layout.addWidget(cancel_btn)
        
        layout.addStretch()
        
        return widget
    
    def _load_styles(self):
        """Загрузить стили."""
        styles_path = Path(__file__).parent / "styles.qss"
        if styles_path.exists():
            with open(styles_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
    
    def _populate_song_list(self):
        """Заполнить список песен."""
        output_dir = get_output_dir()
        
        if not output_dir.exists():
            return
        
        self.songs_list.clear()
        
        for json_file in output_dir.glob("*_karaoke.json"):
            item = QListWidgetItem(json_file.stem.replace("_karaoke", ""))
            item.setData(Qt.UserRole, str(json_file))
            self.songs_list.addItem(item)
    
    def _select_audio_file(self):
        """Выбрать аудиофайл."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать песню",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg);;All Files (*)"
        )
        
        if file_path:
            self.file_label.setText(Path(file_path).name)
            self.file_label.setStyleSheet("color: #cdd6f4;")
            self.file_label.setProperty("path", file_path)
            
            # Автозаполнение названия
            if not self.title_input.text():
                self.title_input.setText(Path(file_path).stem)
    
    def _select_lyrics_file(self):
        """Выбрать текстовый файл."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать текст",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.lyrics_label.setText(Path(file_path).name)
            self.lyrics_label.setStyleSheet("color: #cdd6f4;")
            self.lyrics_label.setProperty("path", file_path)
    
    def _on_lyrics_checkbox_changed(self, state):
        """Обработчик изменения чекбокса текста."""
        self.lyrics_layout.setEnabled(state == Qt.Checked)
    
    def _start_generation(self):
        """Начать генерацию караоке."""
        audio_path = getattr(self.file_label, "property")("path")
        
        if not audio_path or not Path(audio_path).exists():
            QMessageBox.warning(self, "Ошибка", "Выберите аудиофайл")
            return
        
        lyrics_path = None
        if self.has_lyrics_checkbox.isChecked():
            lyrics_path = getattr(self.lyrics_label, "property")("path")
        
        title = self.title_input.text() or Path(audio_path).stem
        artist = self.artist_input.text() or "Unknown"
        
        # Переключаемся на экран генерации
        self.stack.setCurrentIndex(1)
        
        # Запускаем worker
        self.generator_worker = GeneratorWorker(audio_path, lyrics_path, title, artist)
        self.generator_worker.progress.connect(self._on_generation_progress)
        self.generator_worker.finished.connect(self._on_generation_finished)
        self.generator_worker.error.connect(self._on_generation_error)
        self.generator_worker.start()
    
    def _on_generation_progress(self, percent: float, message: str):
        """Обновление прогресса генерации."""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)
    
    def _on_generation_finished(self, karaoke_path: str):
        """Генерация завершена."""
        QMessageBox.information(self, "Готово!", f"Караоке сохранено:\n{karaoke_path}")
        self._populate_song_list()
        self.stack.setCurrentIndex(0)
    
    def _on_generation_error(self, error: str):
        """Ошибка генерации."""
        QMessageBox.critical(self, "Ошибка", f"Ошибка генерации:\n{error}")
        self.stack.setCurrentIndex(0)
    
    def _cancel_generation(self):
        """Отменить генерацию."""
        if self.generator_worker and self.generator_worker.isRunning():
            self.generator_worker.terminate()
            self.generator_worker.wait()
        self.stack.setCurrentIndex(0)
    
    def _open_karaoke_file(self):
        """Открыть караоке-файл."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть караоке",
            str(get_output_dir()),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self._load_karaoke(file_path)
    
    def _on_song_double_clicked(self, item: QListWidgetItem):
        """Двойной клик по песне в списке."""
        karaoke_path = item.data(Qt.UserRole)
        if karaoke_path:
            self._load_karaoke(karaoke_path)
    
    def _load_karaoke(self, path: str):
        """Загрузить караоке и перейти к плееру."""
        # Здесь будет переход на экран караоке
        # Пока просто показываем сообщение
        QMessageBox.information(self, "Инфо", f"Будет загружено: {path}")
