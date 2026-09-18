"""Тесты для VocalScorer."""

import unittest
from src.player.scorer import VocalScorer, cents_to_hz, hz_to_cents


class TestVocalScorer(unittest.TestCase):
    
    def setUp(self):
        self.scorer = VocalScorer(hit_threshold_cents=50)
    
    def test_reset(self):
        """Тест сброса статистики."""
        self.scorer.total_vocal_time_ms = 100
        self.scorer.matched_time_ms = 50
        self.scorer.reset()
        
        self.assertEqual(self.scorer.total_vocal_time_ms, 0.0)
        self.assertEqual(self.scorer.matched_time_ms, 0.0)
    
    def test_evaluate_hit(self):
        """Тест попадания в ноту."""
        # 440 Hz и 445 Hz - отклонение ~20 центов (попадание)
        hit, deviation = self.scorer.evaluate(
            position_sec=1.0,
            target_pitch_hz=440.0,
            actual_pitch_hz=445.0,
            line_index=0
        )
        
        self.assertTrue(hit)
        self.assertLess(abs(deviation), 50)
    
    def test_evaluate_miss(self):
        """Тест промаха."""
        # 440 Hz и 470 Hz - отклонение ~115 центов (промах)
        hit, deviation = self.scorer.evaluate(
            position_sec=1.0,
            target_pitch_hz=440.0,
            actual_pitch_hz=470.0,
            line_index=0
        )
        
        self.assertFalse(hit)
        self.assertGreater(abs(deviation), 50)
    
    def test_evaluate_silence(self):
        """Тест тишины."""
        hit, deviation = self.scorer.evaluate(
            position_sec=1.0,
            target_pitch_hz=0.0,
            actual_pitch_hz=440.0,
            line_index=0
        )
        
        self.assertFalse(hit)
        self.assertEqual(deviation, 0.0)
    
    def test_score_percent(self):
        """Тест процента попадания."""
        # Симулируем 10 измерений: 7 попаданий, 3 промаха
        for i in range(7):
            self.scorer.evaluate(1.0 + i * 0.1, 440.0, 442.0, 0)
        
        for i in range(3):
            self.scorer.evaluate(2.0 + i * 0.1, 440.0, 500.0, 0)
        
        score = self.scorer.get_score_percent()
        
        # Ожидаем около 70%
        self.assertAlmostEqual(score, 70.0, delta=5.0)
    
    def test_cents_conversion(self):
        """Тест конвертации центов."""
        # 100 центов = 1 полутон
        hz = cents_to_hz(100, 440.0)
        self.assertAlmostEqual(hz, 440.0 * (2 ** (1/12)), places=2)
        
        # Обратная конвертация
        cents = hz_to_cents(hz, 440.0)
        self.assertAlmostEqual(cents, 100.0, places=2)


if __name__ == "__main__":
    unittest.main()
