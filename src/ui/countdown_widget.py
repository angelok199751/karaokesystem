"""Виджет обратного отсчёта."""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont

from ..config import COUNTDOWN_MIN_DURATION_SEC, COUNTDOWN_VALUES


class CountdownWidget(QLabel):
    """Виджет обратного отсчёта "3-2-1-Пой!"."""
    
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Стиль
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 46, 0.95);
                color: #f9e2af;
                font-size: 96px;
                font-weight: bold;
                border-radius: 16px;
                padding: 40px;
            }
        """)
        
        # Таймер
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        
        # Состояние
        self.countdown_values = COUNTDOWN_VALUES
        self.current_index = 0
        self.interval_ms = 1000  # 1 секунда
        
        self.hide()
    
    def start_countdown(self, duration_sec: float = None) -> None:
        """
        Начать обратный отсчёт.
        
        Args:
            duration_sec: Длительность паузы (если None, используется стандартная)
        """
        if duration_sec and duration_sec < COUNTDOWN_MIN_DURATION_SEC:
            return
        
        self.current_index = 0
        self.show()
        self._update_display()
        
        self.timer.start(self.interval_ms)
    
    def _on_timeout(self) -> None:
        """Обработчик таймера."""
        self.current_index += 1
        
        if self.current_index >= len(self.countdown_values):
            self.stop()
            self.finished.emit()
        else:
            self._update_display()
    
    def _update_display(self) -> None:
        """Обновить отображение."""
        if self.current_index < len(self.countdown_values):
            value = self.countdown_values[self.current_index]
            self.setText(value)
            
            # Анимация цвета для "Пой!"
            if value == "Пой!":
                self.setStyleSheet("""
                    QLabel {
                        background-color: rgba(166, 227, 161, 0.95);
                        color: #1e1e2e;
                        font-size: 96px;
                        font-weight: bold;
                        border-radius: 16px;
                        padding: 40px;
                    }
                """)
    
    def stop(self) -> None:
        """Остановить обратный отсчёт."""
        self.timer.stop()
        self.hide()
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 46, 0.95);
                color: #f9e2af;
                font-size: 96px;
                font-weight: bold;
                border-radius: 16px;
                padding: 40px;
            }
        """)
