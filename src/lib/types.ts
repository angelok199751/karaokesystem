export interface WordTiming {
  text: string;
  start: number;
  end: number;
}

export interface LyricLine {
  text: string;
  start: number;
  end: number;
  words?: WordTiming[];
}

export interface KaraokeManifest {
  format: string;
  version: number;
  title: string;
  artist?: string;
  author?: string;
  duration: number;
  audio: string;
  lyrics: string;
  bpm?: number;
  key?: string;
  genre?: string;
  cover?: string;
}

export interface KaraokeData {
  version: number;
  title: string;
  duration: number;
  lyrics: LyricLine[];
}

export interface AudioInfo {
  file: File;
  name: string;
  duration: number;
  size: number;
  buffer: AudioBuffer;
}

export interface ProcessingStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'done' | 'error';
  progress?: number;
}

export type AppState = 'input' | 'processing' | 'result' | 'error';
