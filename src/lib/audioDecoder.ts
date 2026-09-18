import { AudioInfo } from './types';

export async function decodeAudio(file: File): Promise<AudioInfo> {
  const arrayBuffer = await file.arrayBuffer();
  
  const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  
  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    return {
      file,
      name: file.name,
      duration: audioBuffer.duration,
      size: file.size,
      buffer: audioBuffer,
    };
  } finally {
    // Don't close the context - we need it for playback
  }
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
