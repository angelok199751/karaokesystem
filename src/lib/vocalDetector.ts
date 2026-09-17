/**
 * Vocal Detection Module
 * 
 * Uses energy-based analysis to detect vocal segments in audio.
 * This is a simplified approach suitable for MVP.
 * The algorithm analyzes RMS energy and spectral characteristics
 * to identify segments where vocals are likely present.
 */

interface VocalSegment {
  start: number;
  end: number;
  energy: number;
}

export interface VocalMap {
  segments: VocalSegment[];
  energyProfile: number[];
  sampleRate: number;
  windowSize: number;
}

/**
 * Detect vocal activity in an audio buffer using energy analysis.
 * This uses a combination of:
 * - RMS energy analysis
 * - Spectral centroid (vocals tend to have specific frequency characteristics)
 * - Temporal smoothing to avoid rapid on/off switching
 */
export async function detectVocals(
  audioBuffer: AudioBuffer,
  onProgress?: (progress: number) => void
): Promise<VocalMap> {
  const sampleRate = audioBuffer.sampleRate;
  const channelData = audioBuffer.getChannelData(0);
  
  // Window size: 20ms windows for analysis
  const windowSize = Math.floor(sampleRate * 0.02);
  const hopSize = Math.floor(windowSize / 2); // 50% overlap
  const numWindows = Math.floor((channelData.length - windowSize) / hopSize);
  
  // Calculate energy profile
  const energyProfile: number[] = [];
  const spectralCentroids: number[] = [];
  
  for (let i = 0; i < numWindows; i++) {
    const start = i * hopSize;
    let sumSquares = 0;
    let weightedSum = 0;
    let totalMagnitude = 0;
    
    for (let j = 0; j < windowSize; j++) {
      const sample = channelData[start + j] || 0;
      sumSquares += sample * sample;
    }
    
    const rms = Math.sqrt(sumSquares / windowSize);
    energyProfile.push(rms);
    
    // Simplified spectral centroid using zero-crossing rate as proxy
    let zeroCrossings = 0;
    for (let j = 1; j < windowSize; j++) {
      const curr = channelData[start + j] || 0;
      const prev = channelData[start + j - 1] || 0;
      if ((curr >= 0 && prev < 0) || (curr < 0 && prev >= 0)) {
        zeroCrossings++;
      }
    }
    spectralCentroids.push(zeroCrossings / windowSize);
    
    if (onProgress && i % 100 === 0) {
      onProgress(i / numWindows * 0.5);
    }
    
    // Yield to main thread periodically
    if (i % 1000 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
  
  // Calculate adaptive threshold
  const sortedEnergy = [...energyProfile].sort((a, b) => a - b);
  const medianEnergy = sortedEnergy[Math.floor(sortedEnergy.length / 2)];
  const maxEnergy = sortedEnergy[sortedEnergy.length - 1];
  
  // Vocal range: typically 80Hz - 1000Hz fundamental
  // Zero crossing rate for this range at 44100 sampleRate: ~0.004 - 0.045
  const vocalZCRMin = 0.002;
  const vocalZCRMax = 0.05;
  
  // Determine threshold: energy above median + some factor
  const threshold = medianEnergy + (maxEnergy - medianEnergy) * 0.3;
  
  // Classify each window as vocal or not
  const isVocal: boolean[] = [];
  for (let i = 0; i < numWindows; i++) {
    const energy = energyProfile[i];
    const zcr = spectralCentroids[i];
    
    // Vocal if: sufficient energy AND in vocal frequency range
    const hasEnergy = energy > threshold;
    const inVocalRange = zcr > vocalZCRMin && zcr < vocalZCRMax;
    
    isVocal.push(hasEnergy && inVocalRange);
  }
  
  // Smooth the classification (median filter)
  const smoothed = medianFilter(isVocal, 5);
  
  // Extract segments
  const segments: VocalSegment[] = [];
  let inSegment = false;
  let segStart = 0;
  let segEnergy = 0;
  let segCount = 0;
  
  for (let i = 0; i < smoothed.length; i++) {
    const time = (i * hopSize) / sampleRate;
    
    if (smoothed[i] && !inSegment) {
      inSegment = true;
      segStart = time;
      segEnergy = 0;
      segCount = 0;
    } else if (!smoothed[i] && inSegment) {
      inSegment = false;
      const segEnd = time;
      const duration = segEnd - segStart;
      
      // Filter out very short segments (likely noise)
      if (duration > 0.1) {
        segments.push({
          start: segStart,
          end: segEnd,
          energy: segCount > 0 ? segEnergy / segCount : 0,
        });
      }
    }
    
    if (inSegment) {
      segEnergy += energyProfile[i];
      segCount++;
    }
  }
  
  // Close last segment if still open
  if (inSegment) {
    const segEnd = (smoothed.length * hopSize) / sampleRate;
    const duration = segEnd - segStart;
    if (duration > 0.1) {
      segments.push({
        start: segStart,
        end: segEnd,
        energy: segCount > 0 ? segEnergy / segCount : 0,
      });
    }
  }
  
  // Merge close segments (gap < 0.3s)
  const merged = mergeCloseSegments(segments, 0.3);
  
  if (onProgress) onProgress(1);
  
  return {
    segments: merged,
    energyProfile,
    sampleRate,
    windowSize,
  };
}

function medianFilter(data: boolean[], size: number): boolean[] {
  const result: boolean[] = [];
  const half = Math.floor(size / 2);
  
  for (let i = 0; i < data.length; i++) {
    let trueCount = 0;
    for (let j = -half; j <= half; j++) {
      const idx = Math.max(0, Math.min(data.length - 1, i + j));
      if (data[idx]) trueCount++;
    }
    result.push(trueCount > size / 2);
  }
  
  return result;
}

function mergeCloseSegments(segments: VocalSegment[], minGap: number): VocalSegment[] {
  if (segments.length <= 1) return segments;
  
  const merged: VocalSegment[] = [segments[0]];
  
  for (let i = 1; i < segments.length; i++) {
    const prev = merged[merged.length - 1];
    const curr = segments[i];
    
    if (curr.start - prev.end < minGap) {
      prev.end = curr.end;
      prev.energy = (prev.energy + curr.energy) / 2;
    } else {
      merged.push(curr);
    }
  }
  
  return merged;
}
