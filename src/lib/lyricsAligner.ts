import { LyricLine } from './types';
import { VocalMap } from './vocalDetector';

/**
 * Lyrics Alignment Module
 * 
 * Maps text lines to vocal segments detected in the audio.
 * Strategy:
 * 1. Parse lyrics into non-empty lines
 * 2. Match lines to vocal segments proportionally
 * 3. Handle cases where segment count differs from line count
 */

export interface AlignmentResult {
  lines: LyricLine[];
  unmatchedSegments: number;
  unmatchedLines: number;
}

export function alignLyrics(
  rawText: string,
  vocalMap: VocalMap,
  duration: number,
  onProgress?: (progress: number) => void
): AlignmentResult {
  // Parse lyrics - split by newlines, keep empty lines as section markers
  const allLines = rawText.split('\n');
  const nonEmptyLines = allLines.filter(line => line.trim().length > 0);
  
  const segments = vocalMap.segments;
  
  if (segments.length === 0) {
    // Fallback: distribute lines evenly across the duration
    return fallbackAlignment(nonEmptyLines, duration);
  }
  
  // Calculate total vocal time
  const totalVocalTime = segments.reduce((sum, seg) => sum + (seg.end - seg.start), 0);
  
  const lines: LyricLine[] = [];
  
  if (segments.length >= nonEmptyLines.length) {
    // More segments than lines: distribute segments among lines
    const segmentsPerLine = Math.ceil(segments.length / nonEmptyLines.length);
    
    for (let i = 0; i < nonEmptyLines.length; i++) {
      const startIdx = i * segmentsPerLine;
      const endIdx = Math.min(startIdx + segmentsPerLine, segments.length);
      
      if (startIdx >= segments.length) break;
      
      const lineStart = segments[startIdx].start;
      const lineEnd = segments[endIdx - 1].end;
      
      lines.push({
        text: nonEmptyLines[i].trim(),
        start: Math.round(lineStart * 100) / 100,
        end: Math.round(lineEnd * 100) / 100,
      });
      
      if (onProgress) onProgress(i / nonEmptyLines.length);
    }
  } else {
    // More lines than segments: distribute lines among segments proportionally
    // Use energy-weighted distribution
    const totalEnergy = segments.reduce((sum, seg) => sum + seg.energy, 0);
    
    let currentSegment = 0;
    let linesAssigned = 0;
    
    for (let i = 0; i < segments.length && linesAssigned < nonEmptyLines.length; i++) {
      const seg = segments[i];
      const segDuration = seg.end - seg.start;
      const segWeight = totalEnergy > 0 ? seg.energy / totalEnergy : 1 / segments.length;
      
      // How many lines should this segment get?
      const linesForSegment = Math.max(1, Math.round(segWeight * nonEmptyLines.length));
      
      const linesStart = linesAssigned;
      const linesEnd = Math.min(linesAssigned + linesForSegment, nonEmptyLines.length);
      const actualLines = linesEnd - linesStart;
      
      if (actualLines > 0 && segDuration > 0) {
        const timePerLine = segDuration / actualLines;
        
        for (let j = 0; j < actualLines; j++) {
          const lineStart = seg.start + j * timePerLine;
          const lineEnd = seg.start + (j + 1) * timePerLine;
          
          lines.push({
            text: nonEmptyLines[linesStart + j].trim(),
            start: Math.round(lineStart * 100) / 100,
            end: Math.round(lineEnd * 100) / 100,
          });
          
          linesAssigned++;
        }
      }
      
      if (onProgress) onProgress(i / segments.length);
    }
    
    // Handle remaining lines
    while (linesAssigned < nonEmptyLines.length) {
      const lastLine = lines.length > 0 ? lines[lines.length - 1] : null;
      const startTime = lastLine ? lastLine.end + 0.1 : 0;
      const endTime = Math.min(startTime + 2, duration);
      
      lines.push({
        text: nonEmptyLines[linesAssigned].trim(),
        start: Math.round(startTime * 100) / 100,
        end: Math.round(endTime * 100) / 100,
      });
      linesAssigned++;
    }
  }
  
  return {
    lines,
    unmatchedSegments: Math.max(0, segments.length - nonEmptyLines.length),
    unmatchedLines: Math.max(0, nonEmptyLines.length - segments.length),
  };
}

function fallbackAlignment(
  lines: string[],
  duration: number
): AlignmentResult {
  // Skip first 10% of audio (intro) and last 5% (outro)
  const startTime = duration * 0.1;
  const endTime = duration * 0.95;
  const availableTime = endTime - startTime;
  
  const timePerLine = availableTime / lines.length;
  const result: LyricLine[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    result.push({
      text: lines[i].trim(),
      start: Math.round((startTime + i * timePerLine) * 100) / 100,
      end: Math.round((startTime + (i + 0.8) * timePerLine) * 100) / 100,
    });
  }
  
  return {
    lines: result,
    unmatchedSegments: 0,
    unmatchedLines: 0,
  };
}
