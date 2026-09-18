"""Экран караоке с текстом и оценкой."""

import json
from pathlib import Path
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QProgressBar, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from ..player.audio_player import AudioPlayer
from ..player.mic_capture import MicCapture
from ..player.realtime_pitch import RealtimePitchDetector
from ..player.scorer import VocalScorer
from .countdown_widget import CountdownWidget


class KaraokeScreen(QWidget):
    """Экран караоке с отображением текста и оценкой."""
    
    finished = Signal()  # Сигнал завершения песни
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.karaoke_data: Optional[Dict] = None
        self.current_line_index = -1
        self.is_playing = False
        
        self._setup_ui()
        
        # Компоненты
        self.audio_player = AudioPlayer()
        self.mic_capture = MicCapture()
        self.pitch_detector = RealtimePitchDetector()
        self.scorer = VocalScorer()
        
        # Таймер обновления UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._on_update_timer)
        self.update_timer.setInterval(100)  # 10 раз в секунду
    
    def _setup_ui(self):
        """Создать интерфейс."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Верхняя панель
        top_panel = QHBoxLayout()
        
        self.title_label = QLabel("Название песни")
        self.title_label.setObjectName("titleLabel")
        top_panel.addWidget(self.title_label)
        
        top_panel.addStretch()
        
        self.pause_btn = QPushButton("⏸ Пауза")
        self.pause_btn.clicked.connect(self._toggle_pause)
        top_panel.addWidget(self.pause_btn)
        
        self.back_btn = QPushButton("← Назад")
        self.back_btn.clicked.connect(self._go_back)
        top_panel.addWidget(self.back_btn)
        
        layout.addLayout(top_panel)
        
        # Область текста
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.text_container = QWidget()
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setAlignment(Qt.AlignCenter)
        self.text_layout.setSpacing(15)
        
        self.line_labels: List[QLabel] = []
        self.scroll_area.setWidget(self.text_container)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Виджет обратного отсчёта
        self.countdown = CountdownWidget()
        self.countdown.finished.connect(self._on_countdown_finished)
        # Накладываем поверх
        layout.addWidget(self.countdown)
        
        # Нижняя панель
        bottom_panel = QVBoxLayout()
        
        # VU-метр микрофона
        vu_label = QLabel("🎤 Микрофон:")
        bottom_panel.addWidget(vu_label)
        
        self.vu_meter = QProgressBar()
        self.vu_meter.setMinimum(0)
        self.vu_meter.setMaximum(100)
        self.vu_meter.setValue(0)
        bottom_panel.addWidget(self.vu_meter)
        
        # Индикатор попадания
        hit_label = QLabel("Попадание:")
        bottom_panel.addWidget(hit_label)
        
        self.hit_indicator = QLabel("—")
        self.hit_indicator.setAlignment(Qt.AlignCenter)
        self.hit_indicator.setStyleSheet("""
            QLabel {
                background-color: #313244;
                color: #cdd6f4;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
            }
        """)
        bottom_panel.addWidget(self.hit_indicator)
        
        # Процент
        self.score_label = QLabel("0%")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #89b4fa;
                padding: 10px;
            }
        """)
        bottom_panel.addWidget(self.score_label)
        
        layout.addLayout(bottom_panel)
    
    def load_karaoke(self, karaoke_path: str) -> None:
        """Загрузить караоке-файл."""
        with open(karaoke_path, "r", encoding="utf-8") as f:
            self.karaoke_data = json.load(f)
        
        # Обновляем заголовок
        title = self.karaoke_data.get("title", "Unknown")
        artist = self.karaoke_data.get("artist", "")
        self.title_label.setText(f"{title} - {artist}")
        
        # Загружаем минус
        karaoke_dir = Path(karaoke_path).parent
        minus_file = self.karaoke_data.get("minus_file", "")
        minus_path = karaoke_dir / minus_file
        
        if minus_path.exists():
            self.audio_player.load(str(minus_path))
        
        # Создаём лейблы для строк
        self._create_line_labels()
        
        # Сбрасываем scorer
        self.scorer.reset()
    
    def _create_line_labels(self):
        """Создать лейблы для строк текста."""
        # Очищаем старые
        for label in self.line_labels:
            label.deleteLater()
        self.line_labels.clear()
        
        if not self.karaoke_data or "lyrics" not in self.karaoke_data:
            return
        
        for line_data in self.karaoke_data["lyrics"]:
            label = QLabel(line_data["text"])
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    color: #6c7086;
                    font-size: 18px;
                    padding: 5px;
                }
            """)
            label.setProperty("line_index", line_data["line_index"])
            label.setProperty("start_sec", line_data["start_sec"])
            label.setProperty("end_sec", line_data["end_sec"])
            
            self.text_layout.addWidget(label)
            self.line_labels.append(label)
    
    def start(self) -> None:
        """Начать воспроизведение."""
        if not self.karaoke_data:
            return
        
        self.is_playing = True
        self.audio_player.play()
        
        # Запускаем захват микрофона
        self.mic_capture.start(self._on_mic_audio)
        
        # Запускаем таймер обновления
        self.update_timer.start()
        
        # Подключаем сигналы плеера
        self.audio_player.position_changed.connect(self._on_position_changed)
        self.audio_player.playback_state_changed.connect(self._on_playback_state_changed)
    
    def stop(self) -> None:
        """Остановить воспроизведение."""
        self.is_playing = False
        self.audio_player.stop()
        self.mic_capture.stop()
        self.update_timer.stop()
        
        # Отключаем сигналы
        try:
            self.audio_player.position_changed.disconnect(self._on_position_changed)
            self.audio_player.playback_state_changed.disconnect(self._on_playback_state_changed)
        except:
            pass
    
    def _on_mic_audio(self, audio_block):
        """Обработка аудио с микрофона."""
        # Определяем pitch
        pitch_hz = self.pitch_detector.detect(audio_block)
        
        # Обновляем VU-метр
        rms = self.mic_capture.get_rms(audio_block)
        vu_value = min(100, int(rms * 200))
        self.vu_meter.setValue(vu_value)
        
        # Сохраняем pitch для обработки в таймере
        self.last_pitch_hz = pitch_hz
    
    def _on_update_timer(self):
        """Таймер обновления UI."""
        if not self.is_playing or not self.karaoke_data:
            return
        
        position = self.audio_player.get_position()
        
        # Находим текущую строку
        self._update_current_line(position)
        
        # Оцениваем пение
        self._evaluate_singing(position)
        
        # Проверяем паузы для countdown
        self._check_pauses(position)
        
        # Проверяем окончание песни
        duration = self.karaoke_data.get("duration_sec", 0)
        if position >= duration - 0.5:
            self._on_song_finished()
    
    def _update_current_line(self, position: float):
        """Обновить подсветку текущей строки."""
        if not self.karaoke_data or "lyrics" not in self.karaoke_data:
            return
        
        new_line_index = -1
        
        for i, line_data in enumerate(self.karaoke_data["lyrics"]):
            start = line_data["start_sec"]
            end = line_data["end_sec"]
            
            if start <= position <= end:
                new_line_index = i
                break
        
        if new_line_index != self.current_line_index:
            self.current_line_index = new_line_index
            
            # Обновляем стили
            for i, label in enumerate(self.line_labels):
                if i == new_line_index:
                    label.setStyleSheet("""
                        QLabel {
                            color: #f9e2af;
                            font-size: 36px;
                            font-weight: bold;
                            padding: 10px;
                        }
                    """)
                elif i < new_line_index:
                    label.setStyleSheet("""
                        QLabel {
                            color: #6c7086;
                            font-size: 18px;
                            padding: 5px;
                        }
                    """)
                else:
                    label.setStyleSheet("""
                        QLabel {
                            color: #6c7086;
                            font-size: 18px;
                            padding: 5px;
                        }
                    """)
            
            # Прокручиваем к текущей строке
            if 0 <= new_line_index < len(self.line_labels):
                self.line_labels[new_line_index].ensureVisible()
    
    def _evaluate_singing(self, position: float):
        """Оценить пение."""
        if self.current_line_index < 0 or not hasattr(self, 'last_pitch_hz'):
            return
        
        # Получаем target pitch для текущей позиции
        target_pitch = self._get_target_pitch_at(position)
        actual_pitch = getattr(self, 'last_pitch_hz', 0)
        
        if target_pitch > 0 and actual_pitch > 0:
            hit, deviation = self.scorer.evaluate(
                position,
                target_pitch,
                actual_pitch,
                self.current_line_index
            )
            
            # Обновляем индикатор
            if hit:
                self.hit_indicator.setText("✓ ПОПАДАНИЕ")
                self.hit_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #a6e3a1;
                        color: #1e1e2e;
                        font-size: 24px;
                        font-weight: bold;
                        padding: 10px;
                        border-radius: 8px;
                    }
                """)
            else:
                self.hit_indicator.setText("✗ МИМО")
                self.hit_indicator.setStyleSheet("""
                    QLabel {
                        background-color: #f38ba8;
                        color: #1e1e2e;
                        font-size: 24px;
                        font-weight: bold;
                        padding: 10px;
                        border-radius: 8px;
                    }
                """)
        else:
            self.hit_indicator.setText("—")
            self.hit_indicator.setStyleSheet("""
                QLabel {
                    background-color: #313244;
                    color: #cdd6f4;
                    font-size: 24px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 8px;
                }
            """)
        
        # Обновляем процент
        score = self.scorer.get_score_percent()
        self.score_label.setText(f"{score:.0f}%")
    
    def _get_target_pitch_at(self, position: float) -> float:
        """Получить целевую частоту в данной позиции."""
        if not self.karaoke_data or "pitch_contour" not in self.karaoke_data:
            return 0.0
        
        contour = self.karaoke_data["pitch_contour"]
        step_ms = contour.get("step_ms", 10)
        frequencies = contour.get("frequencies_hz", [])
        
        if not frequencies:
            return 0.0
        
        index = int(position * 1000 / step_ms)
        
        if 0 <= index < len(frequencies):
            return float(frequencies[index])
        
        return 0.0
    
    def _check_pauses(self, position: float):
        """Проверить паузы для обратного отсчёта."""
        if not self.karaoke_data or "pauses" not in self.karaoke_data:
            return
        
        for pause in self.karaoke_data["pauses"]:
            start = pause["start_sec"]
            end = pause["end_sec"]
            duration = pause["duration_sec"]
            
            # Если мы в начале паузы и нужно показать countdown
            if pause.get("show_countdown") and start <= position < start + 0.5:
                if not self.countdown.isVisible():
                    self.countdown.start_countdown(duration)
    
    def _on_countdown_finished(self):
        """Countdown завершён."""
        pass  # Можно добавить звук или эффект
    
    def _on_position_changed(self, position: float):
        """Изменение позиции воспроизведения."""
        pass
    
    def _on_playback_state_changed(self, is_playing: bool):
        """Изменение состояния воспроизведения."""
        if is_playing:
            self.pause_btn.setText("⏸ Пауза")
        else:
            self.pause_btn.setText("▶ Продолжить")
    
    def _toggle_pause(self):
        """Переключить паузу."""
        if self.audio_player.is_playing():
            self.audio_player.pause()
        else:
            self.audio_player.play()
    
    def _go_back(self):
        """Вернуться назад."""
        self.stop()
        self.finished.emit()
    
    def _on_song_finished(self):
        """Песня завершена."""
        self.stop()
        self.finished.emit()
