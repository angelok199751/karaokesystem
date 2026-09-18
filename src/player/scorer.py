"""Движок оценки точности попадания по нотам."""

import math
from typing import List, Dict, Tuple
import numpy as np

from ..config import (
    HIT_THRESHOLD_CENTS,
    CREPE_STEP_SIZE_MS,
)


class VocalScorer:
    """Оценка точности пения."""
    
    def __init__(self, hit_threshold_cents: float = HIT_THRESHOLD_CENTS):
        self.hit_threshold_cents = hit_threshold_cents
        self.total_vocal_time_ms = 0.0
        self.matched_time_ms = 0.0
        self.timeline: List[Dict] = []
        self.line_scores: Dict[int, Dict] = {}
    
    def reset(self) -> None:
        """Сбросить статистику."""
        self.total_vocal_time_ms = 0.0
        self.matched_time_ms = 0.0
        self.timeline = []
        self.line_scores = {}
    
    def evaluate(
        self,
        position_sec: float,
        target_pitch_hz: float,
        actual_pitch_hz: float,
        line_index: int = -1
    ) -> Tuple[bool, float]:
        """
        Оценить одно измерение.
        
        Args:
            position_sec: Текущая позиция воспроизведения
            target_pitch_hz: Целевая частота из караоке-файла
            actual_pitch_hz: Частота с микрофона
            line_index: Индекс текущей строки
        
        Returns:
            (hit, deviation_cents)
        """
        # Если пауза или тишина - не оцениваем
        if target_pitch_hz == 0 or actual_pitch_hz == 0:
            return False, 0.0
        
        # Вычисляем отклонение в центах
        deviation_cents = 1200 * math.log2(actual_pitch_hz / target_pitch_hz)
        
        # Определяем попадание
        hit = abs(deviation_cents) <= self.hit_threshold_cents
        
        # Обновляем статистику
        interval_ms = CREPE_STEP_SIZE_MS * 10  # Оцениваем 10 раз в секунду
        self.total_vocal_time_ms += interval_ms
        
        if hit:
            self.matched_time_ms += interval_ms
        
        # Записываем в таймлайн
        self.timeline.append({
            "time_sec": round(position_sec, 2),
            "target_hz": round(target_pitch_hz, 1),
            "actual_hz": round(actual_pitch_hz, 1),
            "deviation_cents": round(deviation_cents, 1),
            "hit": hit
        })
        
        # Обновляем статистику по строке
        if line_index >= 0:
            if line_index not in self.line_scores:
                self.line_scores[line_index] = {
                    "total_ms": 0.0,
                    "matched_ms": 0.0
                }
            
            self.line_scores[line_index]["total_ms"] += interval_ms
            if hit:
                self.line_scores[line_index]["matched_ms"] += interval_ms
        
        return hit, deviation_cents
    
    def get_score_percent(self) -> float:
        """Получить общий процент попадания."""
        if self.total_vocal_time_ms == 0:
            return 0.0
        
        return (self.matched_time_ms / self.total_vocal_time_ms) * 100
    
    def get_line_scores(self) -> List[Dict]:
        """Получить оценку по строкам."""
        result = []
        
        for line_idx, scores in sorted(self.line_scores.items()):
            if scores["total_ms"] > 0:
                score_pct = (scores["matched_ms"] / scores["total_ms"]) * 100
            else:
                score_pct = 0.0
            
            result.append({
                "line_index": line_idx,
                "score_percent": round(score_pct, 1)
            })
        
        return result
    
    def get_results_json(self, karaoke_file: str) -> Dict:
        """Сгенерировать JSON результатов."""
        return {
            "karaoke_file": karaoke_file,
            "score_percent": round(self.get_score_percent(), 1),
            "total_vocal_duration_sec": round(self.total_vocal_time_ms / 1000, 1),
            "matched_duration_sec": round(self.matched_time_ms / 1000, 1),
            "breakdown": self.get_line_scores(),
            "pitch_timeline": self.timeline[-1000:]  # Последние 1000 измерений
        }


def cents_to_hz(cents: float, base_hz: float) -> float:
    """Конвертировать центы в Гц."""
    return base_hz * (2 ** (cents / 1200))


def hz_to_cents(hz: float, base_hz: float) -> float:
    """Конвертировать Гц в центы относительно базовой частоты."""
    return 1200 * math.log2(hz / base_hz)
