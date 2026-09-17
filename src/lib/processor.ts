import { AudioInfo, LyricLine, ProcessingStep } from './types';
import { detectVocals, VocalMap } from './vocalDetector';
import { alignLyrics } from './lyricsAligner';
import { buildKaraokeFile } from './karaokeBuilder';

export interface ProcessingResult {
  lyrics: LyricLine[];
  karaokeBlob: Blob;
  vocalMap: VocalMap;
}

export type ProgressCallback = (steps: ProcessingStep[]) => void;

export async function processKaraoke(
  audioInfo: AudioInfo,
  rawText: string,
  title: string,
  onProgress: ProgressCallback
): Promise<ProcessingResult> {
  const steps: ProcessingStep[] = [
    { id: 'decode', label: 'Подготовка аудио...', status: 'pending' },
    { id: 'structure', label: 'Определение структуры текста...', status: 'pending' },
    { id: 'vocal', label: 'Анализ вокала...', status: 'pending' },
    { id: 'sync', label: 'Синхронизация текста...', status: 'pending' },
    { id: 'build', label: 'Создание караоке-файла...', status: 'pending' },
  ];

  onProgress([...steps]);

  // Step 1: Audio is already decoded
  steps[0].status = 'done';
  steps[0].progress = 100;
  onProgress([...steps]);

  // Step 2: Parse text structure
  steps[1].status = 'active';
  onProgress([...steps]);
  
  await new Promise(resolve => setTimeout(resolve, 300));
  
  const lines = rawText.split('\n').filter(l => l.trim().length > 0);
  steps[1].status = 'done';
  steps[1].progress = 100;
  onProgress([...steps]);

  // Step 3: Vocal detection
  steps[2].status = 'active';
  onProgress([...steps]);
  
  const vocalMap = await detectVocals(audioInfo.buffer, (progress) => {
    steps[2].progress = Math.round(progress * 100);
    onProgress([...steps]);
  });
  
  steps[2].status = 'done';
  steps[2].progress = 100;
  onProgress([...steps]);

  // Step 4: Lyrics alignment
  steps[3].status = 'active';
  onProgress([...steps]);
  
  const alignment = alignLyrics(rawText, vocalMap, audioInfo.duration, (progress) => {
    steps[3].progress = Math.round(progress * 100);
    onProgress([...steps]);
  });
  
  // Post-process: add preview time for karaoke display
  // Show first line 1.5s before vocal starts
  if (alignment.lines.length > 0 && alignment.lines[0].start > 0.3) {
    alignment.lines[0].start = Math.max(0, alignment.lines[0].start - 1.5);
  }
  
  // Add preview time between lines with gaps
  for (let i = 1; i < alignment.lines.length; i++) {
    const line = alignment.lines[i];
    const prevLine = alignment.lines[i - 1];
    const gap = line.start - prevLine.end;
    
    if (gap > 0.5) {
      alignment.lines[i].start = Math.max(prevLine.end + 0.1, line.start - 0.8);
    }
  }
  
  steps[3].status = 'done';
  steps[3].progress = 100;
  onProgress([...steps]);

  // Step 5: Build karaoke file
  steps[4].status = 'active';
  onProgress([...steps]);
  
  // Use original file as audio blob for best quality
  const karaokeBlob = await buildKaraokeFile({
    title,
    duration: audioInfo.duration,
    lyrics: alignment.lines,
    audioBlob: audioInfo.file,
    audioFileName: audioInfo.name,
  });
  
  steps[4].status = 'done';
  steps[4].progress = 100;
  onProgress([...steps]);

  return {
    lyrics: alignment.lines,
    karaokeBlob,
    vocalMap,
  };
}
