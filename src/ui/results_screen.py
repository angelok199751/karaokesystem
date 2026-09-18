"""Экран результатов пения."""

import json
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ResultsScreen(QWidget):
    """Экран отображения результатов пения."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.results_data: Optional[Dict] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Создать интерфейс."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Заголовок
        title_label = QLabel("Результат")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Процент
        self.score_label = QLabel("0%")
        self.score_label.setObjectName("scoreLabel")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)
        
        # Текстовая оценка
        self.text_evaluation = QLabel("")
        self.text_evaluation.setAlignment(Qt.AlignCenter)
        self.text_evaluation.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #cdd6f4;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_evaluation)
        
        # Таблица по строкам
        table_label = QLabel("По строкам:")
        layout.addWidget(table_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Текст", "%"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        self.retry_btn = QPushButton("🔄 Спеть ещё раз")
        self.retry_btn.setObjectName("accentButton")
        self.retry_btn.clicked.connect(self._on_retry)
        buttons_layout.addWidget(self.retry_btn)
        
        self.save_btn = QPushButton("💾 Сохранить результат")
        self.save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(self.save_btn)
        
        self.back_btn = QPushButton("← На главную")
        self.back_btn.clicked.connect(self._on_back)
        buttons_layout.addWidget(self.back_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_results(self, results_data: Dict) -> None:
        """Загрузить результаты."""
        self.results_data = results_data
        
        # Процент
        score = results_data.get("score_percent", 0)
        self.score_label.setText(f"{score:.0f}%")
        
        # Цвет и текст оценки
        if score >= 90:
            self.score_label.setProperty("class", "gold")
            self.score_label.setStyleSheet("color: #f9e2af;")
            self.text_evaluation.setText("Отлично! 🌟")
        elif score >= 70:
            self.score_label.setStyleSheet("color: #a6e3a1;")
            self.text_evaluation.setText("Хорошо! 👍")
        elif score >= 50:
            self.score_label.setStyleSheet("color: #f9e2af;")
            self.text_evaluation.setText("Неплохо! 🙂")
        else:
            self.score_label.setStyleSheet("color: #f38ba8;")
            self.text_evaluation.setText("Попробуй ещё раз! 💪")
        
        # Таблица
        breakdown = results_data.get("breakdown", [])
        self.table.setRowCount(len(breakdown))
        
        for i, item in enumerate(breakdown):
            text_item = QTableWidgetItem(item.get("text", f"Строка {i}"))
            score_item = QTableWidgetItem(f"{item.get('score_percent', 0):.0f}%")
            score_item.setTextAlignment(Qt.AlignCenter)
            
            self.table.setItem(i, 0, text_item)
            self.table.setItem(i, 1, score_item)
    
    def set_karaoke_path(self, path: str) -> None:
        """Установить путь к караоке-файлу."""
        self.karaoke_path = path
    
    def _on_retry(self):
        """Начать заново."""
        # Сигнал будет обработан в main_window
        pass
    
    def _on_save(self):
        """Сохранить результат."""
        if not self.results_data:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.results_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Сохранено", f"Результат сохранён:\n{file_path}")
    
    def _on_back(self):
        """Вернуться на главную."""
        pass
