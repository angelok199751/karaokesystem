import { useCallback, useRef, useState } from 'react';
import { AudioInfo } from '../lib/types';
import { formatDuration, formatFileSize } from '../lib/audioDecoder';

interface AudioInputProps {
  audioInfo: AudioInfo | null;
  onLoaded: (file: File) => void;
  onRemove: () => void;
}

export function AudioInput({ audioInfo, onLoaded, onRemove }: AudioInputProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-m4a', 'audio/mp4', 'audio/ogg', 'audio/x-wav'];
    const validExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (validTypes.includes(file.type) || validExtensions.includes(ext)) {
      onLoaded(file);
    } else {
      alert('Неподдерживаемый формат. Используйте MP3, WAV, M4A или OGG.');
    }
  }, [onLoaded]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  if (audioInfo) {
    return (
      <div className="bg-gray-800/50 backdrop-blur rounded-xl p-5 border border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <span className="text-xl">🎵</span>
            </div>
            <div>
              <p className="text-white font-medium truncate max-w-[250px]">{audioInfo.name}</p>
              <p className="text-gray-400 text-sm">
                {formatDuration(audioInfo.duration)} • {formatFileSize(audioInfo.size)}
              </p>
            </div>
          </div>
          <button
            onClick={onRemove}
            className="text-gray-400 hover:text-red-400 transition-colors p-2"
            title="Удалить"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label className="block text-gray-300 text-sm font-medium mb-2">
        Аудио
      </label>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-purple-400 bg-purple-600/10'
            : 'border-gray-600 hover:border-gray-500 bg-gray-800/30'
        }`}
      >
        <div className="text-4xl mb-3">🎶</div>
        <p className="text-gray-300 mb-1">Перетащите аудиофайл сюда</p>
        <p className="text-gray-500 text-sm">или</p>
        <p className="text-purple-400 font-medium mt-1">Выбрать файл</p>
        <p className="text-gray-600 text-xs mt-3">MP3, WAV, M4A, OGG</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*,.mp3,.wav,.m4a,.ogg,.aac,.flac"
        onChange={handleInputChange}
        className="hidden"
      />
    </div>
  );
}
