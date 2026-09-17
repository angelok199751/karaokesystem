import { useState, useRef, useEffect, useCallback } from 'react';
import { LyricLine } from '../lib/types';
import { formatDuration, formatFileSize } from '../lib/audioDecoder';
import { getKaraokeFileName } from '../lib/karaokeBuilder';
import { saveAs } from 'file-saver';

interface ResultViewProps {
  title: string;
  duration: number;
  lyrics: LyricLine[];
  karaokeBlob: Blob;
  audioFile: File;
  onReset: () => void;
}

export function ResultView({ title, duration, lyrics, karaokeBlob, audioFile, onReset }: ResultViewProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeLineIndex, setActiveLineIndex] = useState(-1);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);
  const lyricsContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Create audio URL
    const url = URL.createObjectURL(audioFile);
    audioUrlRef.current = url;
    const audio = new Audio(url);
    audioRef.current = audio;

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      setActiveLineIndex(-1);
    });

    return () => {
      audio.pause();
      URL.revokeObjectURL(url);
    };
  }, [audioFile]);

  // Update active line based on current time
  useEffect(() => {
    const idx = lyrics.findIndex(
      (line) => currentTime >= line.start && currentTime <= line.end
    );
    setActiveLineIndex(idx);
  }, [currentTime, lyrics]);

  // Scroll active line into view
  useEffect(() => {
    if (activeLineIndex >= 0 && lyricsContainerRef.current) {
      const activeEl = lyricsContainerRef.current.children[activeLineIndex] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeLineIndex]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  }, []);

  const handleDownload = useCallback(() => {
    const fileName = getKaraokeFileName(title);
    saveAs(karaokeBlob, fileName);
  }, [karaokeBlob, title]);

  return (
    <div className="space-y-6">
      {/* Success header */}
      <div className="text-center bg-gray-800/50 backdrop-blur rounded-xl p-6 border border-gray-700">
        <div className="inline-flex items-center justify-center w-14 h-14 bg-green-500/20 rounded-full mb-3">
          <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-1">Караоке готово</h2>
        <p className="text-gray-300 font-medium">{title}</p>
        <div className="flex items-center justify-center gap-4 mt-3 text-sm text-gray-400">
          <span>⏱ {formatDuration(duration)}</span>
          <span>📝 {lyrics.length} строк</span>
          <span>💾 {formatFileSize(karaokeBlob.size)}</span>
        </div>
      </div>

      {/* Player */}
      <div className="bg-gray-800/50 backdrop-blur rounded-xl p-5 border border-gray-700">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={togglePlay}
            className="w-12 h-12 bg-purple-600 hover:bg-purple-500 rounded-full flex items-center justify-center transition-colors shadow-lg shadow-purple-600/20"
          >
            {isPlaying ? (
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>
          
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max={duration}
              step="0.1"
              value={currentTime}
              onChange={handleSeek}
              className="w-full h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-purple-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{formatDuration(currentTime)}</span>
              <span>{formatDuration(duration)}</span>
            </div>
          </div>
        </div>

        {/* Lyrics display */}
        <div 
          ref={lyricsContainerRef}
          className="max-h-64 overflow-y-auto space-y-1 pr-2 scrollbar-thin"
        >
          {lyrics.map((line, idx) => (
            <div
              key={idx}
              className={`px-3 py-1.5 rounded-lg transition-all duration-200 cursor-pointer ${
                idx === activeLineIndex
                  ? 'bg-purple-600/20 text-white font-medium scale-[1.02]'
                  : currentTime >= line.start && currentTime <= line.end
                  ? 'bg-purple-600/10 text-purple-200'
                  : currentTime > line.end
                  ? 'text-gray-500'
                  : 'text-gray-400'
              }`}
              onClick={() => {
                if (audioRef.current) {
                  audioRef.current.currentTime = line.start;
                  setCurrentTime(line.start);
                  if (!isPlaying) {
                    audioRef.current.play();
                    setIsPlaying(true);
                  }
                }
              }}
            >
              <span className="text-xs text-gray-600 mr-2 font-mono">
                {formatDuration(line.start)}
              </span>
              {line.text}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleDownload}
          className="flex-1 py-3 px-6 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold transition-all duration-200 shadow-lg shadow-purple-600/20 active:scale-[0.98]"
        >
          ⬇ Скачать караоке-файл
        </button>
        <button
          onClick={onReset}
          className="py-3 px-6 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-xl font-medium transition-colors"
        >
          Создать ещё
        </button>
      </div>
    </div>
  );
}
