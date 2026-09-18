"""Очистка Pitch Contour: удаление артефактов, сглаживание."""

import numpy as np
from scipy import signal

from ..config import (
    MIN_NOTE_DURATION_MS,
    MAX_GAP_FILL_MS,
    MEDIAN_FILTER_WINDOW,
    CREPE_STEP_SIZE_MS,
)


class PitchCleaner:
    """Очистка и постобработка pitch contour."""
    
    def clean(
        self,
        frequencies: np.ndarray,
        confidence: np.ndarray = None
    ) -> np.ndarray:
        """
        Очистить pitch contour.
        
        Args:
            frequencies: Массив частот (Hz)
            confidence: Массив уверенности (опционально)
        
        Returns:
            Очищенный массив частот
        """
        result = frequencies.copy()
        
        # Шаг в сэмплах массива
        step_samples = 1  # Уже в нужном разрешении
        
        # Удаляем короткие артефакты (< MIN_NOTE_DURATION_MS)
        min_duration_samples = max(1, MIN_NOTE_DURATION_MS // CREPE_STEP_SIZE_MS)
        result = self._remove_short_segments(result, min_duration_samples)
        
        # Заполняем короткие пропуски (< MAX_GAP_FILL_MS)
        max_gap_samples = max(1, MAX_GAP_FILL_MS // CREPE_STEP_SIZE_MS)
        result = self._fill_gaps(result, max_gap_samples)
        
        # Сглаживание медианным фильтром
        window_size = max(3, MEDIAN_FILTER_WINDOW)
        if window_size % 2 == 0:
            window_size += 1  # Должно быть нечётным
        
        result = self._median_filter(result, window_size)
        
        return result
    
    def _remove_short_segments(
        self,
        frequencies: np.ndarray,
        min_samples: int
    ) -> np.ndarray:
        """Удалить сегменты короче min_samples."""
        result = frequencies.copy()
        non_zero = result != 0
        
        # Находим границы сегментов
        edges = np.diff(non_zero.astype(int))
        starts = np.where(edges == 1)[0] + 1
        ends = np.where(edges == -1)[0] + 1
        
        # Обрабатываем края
        if non_zero[0]:
            starts = np.insert(starts, 0, 0)
        if non_zero[-1]:
            ends = np.append(ends, len(result))
        
        # Удаляем короткие сегменты
        for start, end in zip(starts, ends):
            if end - start < min_samples:
                result[start:end] = 0
        
        return result
    
    def _fill_gaps(
        self,
        frequencies: np.ndarray,
        max_gap_samples: int
    ) -> np.ndarray:
        """Заполнить короткие пропуски линейной интерполяцией."""
        result = frequencies.copy()
        non_zero = result != 0
        
        # Находим нулевые сегменты
        edges = np.diff(non_zero.astype(int))
        zero_starts = np.where(edges == -1)[0] + 1
        zero_ends = np.where(edges == 1)[0] + 1
        
        # Обрабатываем края
        if not non_zero[0]:
            zero_starts = np.insert(zero_starts, 0, 0)
        if not non_zero[-1]:
            zero_ends = np.append(zero_ends, len(result))
        
        # Заполняем короткие пропуски
        for start, end in zip(zero_starts, zero_ends):
            gap_length = end - start
            
            # Пропуск должен быть между двумя ненулевыми значениями
            if start > 0 and end < len(result) and gap_length <= max_gap_samples:
                start_val = result[start - 1]
                end_val = result[end]
                
                if start_val != 0 and end_val != 0:
                    # Линейная интерполяция
                    result[start:end] = np.linspace(
                        start_val, end_val, gap_length
                    )
        
        return result
    
    def _median_filter(
        self,
        frequencies: np.ndarray,
        window_size: int
    ) -> np.ndarray:
        """Применить медианный фильтр только к ненулевым значениям."""
        result = frequencies.copy()
        non_zero_mask = result != 0
        
        if np.sum(non_zero_mask) < window_size:
            return result
        
        # Применяем фильтр только к ненулевым участкам
        filtered = signal.medfilt(result, kernel_size=window_size)
        
        # Сохраняем нули на местах нулей
        result[non_zero_mask] = filtered[non_zero_mask]
        
        return result
