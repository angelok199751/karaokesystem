"""Воспроизведение аудио с помощью QMediaPlayer."""

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QObject):
    """Воспроизведение минуса."""
    
    position_changed = Signal(float)  # позиция в секундах
    duration_changed = Signal(float)  # длительность в секундах
    playback_state_changed = Signal(bool)  #.isPlaying
    
    def __init__(self):
        super().__init__()
        
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        
        # Подключаем сигналы
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
    
    def _on_position_changed(self, position_ms: int):
        self.position_changed.emit(position_ms / 1000.0)
    
    def _on_duration_changed(self, duration_ms: int):
        self.duration_changed.emit(duration_ms / 1000.0)
    
    def _on_playback_state_changed(self, state):
        from PySide6.QtMultimedia import QMediaPlayer
        is_playing = state == QMediaPlayer.PlayingState
        self.playback_state_changed.emit(is_playing)
    
    def load(self, path: str) -> None:
        """Загрузить аудиофайл."""
        from PySide6.QtCore import QUrl
        self.player.setSource(QUrl.fromLocalFile(path))
    
    def play(self) -> None:
        """Начать воспроизведение."""
        self.player.play()
    
    def pause(self) -> None:
        """Приостановить воспроизведение."""
        self.player.pause()
    
    def stop(self) -> None:
        """Остановить воспроизведение."""
        self.player.stop()
    
    def set_position(self, seconds: float) -> None:
        """Установить позицию воспроизведения."""
        self.player.setPosition(int(seconds * 1000))
    
    def get_position(self) -> float:
        """Получить текущую позицию в секундах."""
        return self.player.position() / 1000.0
    
    def get_duration(self) -> float:
        """Получить длительность в секундах."""
        return self.player.duration() / 1000.0
    
    def is_playing(self) -> bool:
        """Проверить, идёт ли воспроизведение."""
        from PySide6.QtMultimedia import QMediaPlayer
        return self.player.playbackState() == QMediaPlayer.PlayingState
    
    def set_volume(self, volume: float) -> None:
        """Установить громкость (0.0-1.0)."""
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))
