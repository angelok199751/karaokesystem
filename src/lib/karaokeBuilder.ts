import JSZip from 'jszip';
import { KaraokeManifest, KaraokeData, LyricLine } from './types';

/**
 * Karaoke File Builder
 * 
 * Creates a .karaoke file (ZIP container) containing:
 * - manifest.json
 * - audio.mp3 (or original format)
 * - lyrics.json
 */

export interface BuildOptions {
  title: string;
  duration: number;
  lyrics: LyricLine[];
  audioBlob: Blob;
  audioFileName: string;
}

export async function buildKaraokeFile(options: BuildOptions): Promise<Blob> {
  const zip = new JSZip();
  
  // Create manifest
  const manifest: KaraokeManifest = {
    format: 'karaoke',
    version: 1,
    title: options.title,
    duration: options.duration,
    audio: 'audio' + getExtension(options.audioFileName),
    lyrics: 'lyrics.json',
  };
  
  // Create lyrics data
  const karaokeData: KaraokeData = {
    version: 1,
    title: options.title,
    duration: options.duration,
    lyrics: options.lyrics,
  };
  
  // Add files to ZIP
  zip.file('manifest.json', JSON.stringify(manifest, null, 2));
  zip.file('lyrics.json', JSON.stringify(karaokeData, null, 2));
  zip.file('audio' + getExtension(options.audioFileName), options.audioBlob);
  
  // Generate ZIP blob
  const blob = await zip.generateAsync({ 
    type: 'blob',
    compression: 'DEFLATE',
    compressionOptions: { level: 6 }
  });
  
  return blob;
}

function getExtension(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext && ['mp3', 'wav', 'm4a', 'ogg', 'aac', 'flac'].includes(ext)) {
    return '.' + ext;
  }
  return '.mp3';
}

export function getKaraokeFileName(title: string): string {
  // Sanitize title for filename
  const sanitized = title
    .replace(/[<>:"/\\|?*]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  
  return `${sanitized}.karaoke`;
}
