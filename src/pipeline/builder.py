"""Сборка итогового караоке-файла."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import numpy as np
import librosa

from ..config import (
    SAMPLE_RATE,
    CREPE_STEP_SIZE_MS,
    COUNTDOWN_MIN_DURATION_SEC,
)


class KaraokeBuilder:
    """Сборка итогового JSON-файла караоке."""
    
    def build(
        self,
        words: List[Dict],
        pitch_frequencies: np.ndarray,
        instrumental_path: str,
        output_dir: Path,
        title: str = "Unknown",
        artist: str = "Unknown",
        source_file: str = "",
        progress_callback=None
    ) -> str:
        """
        Собрать караоке-файл.
        
        Args:
            words: Список слов с таймкодами
            pitch_frequencies: Массив частот
            instrumental_path: Путь к инструменталу
            output_dir: Директория для выходных файлов
            title: Название песни
            artist: Исполнитель
            source_file: Исходный файл
            progress_callback: Callback для обновления прогресса
        
        Returns:
            Путь к karaoke.json
        """
        # Группируем слова в строки по паузам
        lines = self._group_words_into_lines(words)
        
        if progress_callback:
            progress_callback(0.2)
        
        # Вычисляем target_pitch для каждого слова
        for word in words:
            word["target_pitch_hz"] = self._get_target_pitch(
                word["start_sec"],
                word["end_sec"],
                pitch_frequencies
            )
        
        if progress_callback:
            progress_callback(0.4)
        
        # Определяем паузы между строками
        pauses = self._find_pauses(lines)
        
        if progress_callback:
            progress_callback(0.6)
        
        # Сохраняем минус
        minus_path = output_dir / f"{Path(source_file).stem}_minus.mp3"
        self._convert_to_mp3(instrumental_path, str(minus_path))
        
        if progress_callback:
            progress_callback(0.8)
        
        # Собираем JSON
        karaoke_data = {
            "version": "1.0",
            "title": title,
            "artist": artist,
            "source_file": Path(source_file).name,
            "duration_sec": self._get_total_duration(words, pauses),
            "sample_rate": SAMPLE_RATE,
            "pitch_step_ms": CREPE_STEP_SIZE_MS,
            "minus_file": minus_path.name,
            "lyrics": [
                {
                    "line_index": i,
                    "text": " ".join(w["text"] for w in line["words"]),
                    "start_sec": line["start_sec"],
                    "end_sec": line["end_sec"],
                    "words": line["words"]
                }
                for i, line in enumerate(lines)
            ],
            "pitch_contour": {
                "start_sec": 0.0,
                "step_ms": CREPE_STEP_SIZE_MS,
                "frequencies_hz": pitch_frequencies.tolist()
            },
            "pauses": pauses,
            "metadata": {
                "generator": "KaraokeForge 1.0",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "confidence_avg": self._calc_avg_confidence(words),
                "language": "ru"
            }
        }
        
        # Сохраняем JSON
        karaoke_path = output_dir / f"{Path(source_file).stem}_karaoke.json"
        with open(karaoke_path, "w", encoding="utf-8") as f:
            json.dump(karaoke_data, f, ensure_ascii=False, indent=2)
        
        if progress_callback:
            progress_callback(1.0)
        
        return str(karaoke_path)
    
    def _group_words_into_lines(
        self,
        words: List[Dict],
        pause_threshold: float = 0.5
    ) -> List[Dict]:
        """Сгруппировать слова в строки по паузам."""
        if not words:
            return []
        
        lines = []
        current_line = {"words": [], "start_sec": None, "end_sec": None}
        
        for word in words:
            if not current_line["words"]:
                current_line["words"].append(word)
                current_line["start_sec"] = word["start_sec"]
                current_line["end_sec"] = word["end_sec"]
            else:
                # Проверяем паузу между словами
                gap = word["start_sec"] - current_line["end_sec"]
                
                if gap > pause_threshold:
                    # Новая строка
                    lines.append(current_line)
                    current_line = {
                        "words": [word],
                        "start_sec": word["start_sec"],
                        "end_sec": word["end_sec"]
                    }
                else:
                    current_line["words"].append(word)
                    current_line["end_sec"] = word["end_sec"]
        
        # Добавляем последнюю строку
        if current_line["words"]:
            lines.append(current_line)
        
        return lines
    
    def _find_pauses(
        self,
        lines: List[Dict],
        min_duration: float = COUNTDOWN_MIN_DURATION_SEC
    ) -> List[Dict]:
        """Найти паузы между строками."""
        pauses = []
        
        for i in range(len(lines) - 1):
            current_end = lines[i]["end_sec"]
            next_start = lines[i + 1]["start_sec"]
            
            duration = next_start - current_end
            
            if duration >= min_duration:
                pauses.append({
                    "start_sec": current_end,
                    "end_sec": next_start,
                    "duration_sec": duration,
                    "show_countdown": True
                })
        
        return pauses
    
    def _get_target_pitch(
        self,
        start_sec: float,
        end_sec: float,
        frequencies: np.ndarray
    ) -> float:
        """Вычислить медианную частоту для участка."""
        step_sec = CREPE_STEP_SIZE_MS / 1000.0
        
        start_idx = int(start_sec / step_sec)
        end_idx = int(end_sec / step_sec)
        
        if start_idx >= len(frequencies):
            return 0.0
        
        end_idx = min(end_idx, len(frequencies))
        
        segment = frequencies[start_idx:end_idx]
        non_zero = segment[segment != 0]
        
        if len(non_zero) == 0:
            return 0.0
        
        return float(np.median(non_zero))
    
    def _get_total_duration(
        self,
        words: List[Dict],
        pauses: List[Dict]
    ) -> float:
        """Вычислить общую длительность."""
        if not words and not pauses:
            return 0.0
        
        max_time = 0.0
        
        if words:
            max_time = max(max_time, words[-1]["end_sec"])
        
        if pauses:
            max_time = max(max_time, pauses[-1]["end_sec"])
        
        return max_time
    
    def _calc_avg_confidence(self, words: List[Dict]) -> float:
        """Вычислить среднюю уверенность (заглушка)."""
        # В реальной реализации можно использовать confidence из CREPE
        return 0.8
    
    def _convert_to_mp3(self, input_path: str, output_path: str) -> None:
        """Конвертировать аудио в MP3."""
        from pydub import AudioSegment
        
        audio = AudioSegment.from_wav(input_path)
        audio.export(output_path, format="mp3", bitrate="192k")
