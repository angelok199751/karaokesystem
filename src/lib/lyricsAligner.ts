import { LyricLine } from './types';
import { VocalMap } from './vocalDetector';

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
  const allLines = rawText.split('\n');
  const nonEmptyLines = allLines.filter(line => line.trim().length > 0);
  
  let segments = [...vocalMap.segments];
  
  if (segments.length === 0) {
    return fallbackAlignment(nonEmptyLines, duration);
  }
  
  // Compensate for late vocal detection (moderate adjustment)
  segments = compensateLateStart(segments, vocalMap.energyProfile, vocalMap.sampleRate, vocalMap.windowSize, duration);
  
  return processWithSegments(nonEmptyLines, segments, duration);
}

function processWithSegments(
  nonEmptyLines: string[],
  segments: { start: number; end: number; energy: number }[],
  duration: number
): AlignmentResult {
  const lines: LyricLine[] = [];
  
  if (segments.length >= nonEmptyLines.length) {
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
    }
  } else {
    const totalEnergy = segments.reduce((sum, seg) => sum + seg.energy, 0);
    let linesAssigned = 0;
    
    for (let i = 0; i < segments.length && linesAssigned < nonEmptyLines.length; i++) {
      const seg = segments[i];
      const segDuration = seg.end - seg.start;
      const segWeight = totalEnergy > 0 ? seg.energy / totalEnergy : 1 / segments.length;
      
      const linesForSegment = Math.max(1, Math.round(segWeight * nonEmptyLines.length));
      const linesEnd = Math.min(linesAssigned + linesForSegment, nonEmptyLines.length);
      const actualLines = linesEnd - linesAssigned;
      
      if (actualLines > 0 && segDuration > 0) {
        const timePerLine = segDuration / actualLines;
        
        for (let j = 0; j < actualLines; j++) {
          const lineStart = seg.start + j * timePerLine;
          const lineEnd = seg.start + (j + 1) * timePerLine;
          
          lines.push({
            text: nonEmptyLines[linesAssigned + j].trim(),
            start: Math.round(lineStart * 100) / 100,
            end: Math.round(lineEnd * 100) / 100,
          });
          
          linesAssigned++;
        }
      }
    }
    
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

function compensateLateStart(
  segments: { start: number; end: number; energy: number }[],
  energyProfile: number[],
  sampleRate: number,
  windowSize: number,
  duration: number
): { start: number; end: number; energy: number }[] {
  if (segments.length === 0) return segments;
  
  const hopSize = Math.floor(windowSize / 2);
  const firstSegStart = segments[0].start;
  
  // Only compensate if first segment starts after 5 seconds (clearly late)
  if (firstSegStart < 5) return segments;
  
  const sortedEnergy = [...energyProfile].sort((a, b) => a - b);
  const medianEnergy = sortedEnergy[Math.floor(sortedEnergy.length * 0.5)];
  const threshold = medianEnergy * 1.3;
  
  let firstEnergyIdx = 0;
  for (let i = 0; i < energyProfile.length; i++) {
    if (energyProfile[i] > threshold) {
      let sustained = 0;
      for (let j = i; j < Math.min(i + 20, energyProfile.length); j++) {
        if (energyProfile[j] > threshold) sustained++;
      }
      if (sustained >= 5) {
        firstEnergyIdx = i;
        break;
      }
    }
  }
  
  const firstEnergyTime = (firstEnergyIdx * hopSize) / sampleRate;
  
  // Pull back to where energy actually starts (with small buffer)
  if (firstEnergyTime < firstSegStart - 1) {
    const adjusted = [...segments];
    adjusted[0] = {
      ...adjusted[0],
      start: Math.max(0, firstEnergyTime),
    };
    return adjusted;
  }
  
  return segments;
}

function fallbackAlignment(
  lines: string[],
  duration: number
): AlignmentResult {
  // Skip first 5% for intro
  const startTime = duration * 0.05;
  const endTime = duration * 0.97;
  const availableTime = endTime - startTime;
  
  const timePerLine = availableTime / lines.length;
  const result: LyricLine[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    result.push({
      text: lines[i].trim(),
      start: Math.round((startTime + i * timePerLine) * 100) / 100,
      end: Math.round((startTime + (i + 0.85) * timePerLine) * 100) / 100,
    });
  }
  
  return {
    lines: result,
    unmatchedSegments: 0,
    unmatchedLines: 0,
  };
}
