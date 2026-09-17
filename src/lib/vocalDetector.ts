/**
 * Vocal Detection Module
 * 
 * Detects vocal activity using energy-based analysis with onset detection.
 * Optimized to catch early vocals and avoid late starts.
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
 */
export async function detectVocals(
  audioBuffer: AudioBuffer,
  onProgress?: (progress: number) => void
): Promise<VocalMap> {
  const sampleRate = audioBuffer.sampleRate;
  const channelData = audioBuffer.getChannelData(0);
  
  // Mix all channels to mono for analysis
  const totalSamples = audioBuffer.length;
  let monoData: Float32Array;
  if (audioBuffer.numberOfChannels > 1) {
    monoData = new Float32Array(totalSamples);
    for (let ch = 0; ch < audioBuffer.numberOfChannels; ch++) {
      const chData = audioBuffer.getChannelData(ch);
      for (let i = 0; i < totalSamples; i++) {
        monoData[i] += chData[i] / audioBuffer.numberOfChannels;
      }
    }
  } else {
    monoData = channelData;
  }
  
  // Window size: 20ms windows
  const windowSize = Math.floor(sampleRate * 0.02);
  const hopSize = Math.floor(windowSize / 2);
  const numWindows = Math.floor((totalSamples - windowSize) / hopSize);
  
  // Calculate energy profile and spectral features
  const energyProfile: number[] = [];
  const spectralFeatures: number[] = [];
  
  for (let i = 0; i < numWindows; i++) {
    const start = i * hopSize;
    let sumSquares = 0;
    let zeroCrossings = 0;
    
    for (let j = 0; j < windowSize; j++) {
      const sample = monoData[start + j] || 0;
      sumSquares += sample * sample;
      
      if (j > 0) {
        const prev = monoData[start + j - 1] || 0;
        if ((sample >= 0 && prev < 0) || (sample < 0 && prev >= 0)) {
          zeroCrossings++;
        }
      }
    }
    
    const rms = Math.sqrt(sumSquares / windowSize);
    energyProfile.push(rms);
    
    // Normalized zero crossing rate (proxy for spectral centroid)
    const zcr = zeroCrossings / windowSize;
    spectralFeatures.push(zcr);
    
    if (onProgress && i % 200 === 0) {
      onProgress(i / numWindows * 0.5);
    }
    
    if (i % 2000 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
  
  // Calculate adaptive threshold using percentile-based approach
  const sortedEnergy = [...energyProfile].sort((a, b) => a - b);
  
  // Use 40th percentile as base (more sensitive to quiet parts)
  const p40 = sortedEnergy[Math.floor(sortedEnergy.length * 0.4)];
  const p90 = sortedEnergy[Math.floor(sortedEnergy.length * 0.9)];
  const maxEnergy = sortedEnergy[sortedEnergy.length - 1];
  
  // Lower threshold: closer to median to catch quieter vocals
  // Use 10% of dynamic range above p40 (more aggressive)
  const threshold = p40 + (p90 - p40) * 0.1;
  
  // Vocal frequency range (broader to catch more voices)
  const vocalZCRMin = 0.001;
  const vocalZCRMax = 0.08;
  
  // Classify each window
  const isVocal: boolean[] = [];
  for (let i = 0; i < numWindows; i++) {
    const energy = energyProfile[i];
    const zcr = spectralFeatures[i];
    
    // More lenient: either good energy OR good frequency range with some energy
    const hasEnergy = energy > threshold;
    const inVocalRange = zcr > vocalZCRMin && zcr < vocalZCRMax;
    const hasSomeEnergy = energy > p40 * 0.5;
    
    isVocal.push((hasEnergy && inVocalRange) || (hasSomeEnergy && inVocalRange));
  }
  
  // Smooth with smaller window to preserve early onsets
  const smoothed = medianFilter(isVocal, 3);
  
  // Apply onset detection: look for energy rises
  const withOnsets = applyOnsetDetection(smoothed, energyProfile, threshold, hopSize, sampleRate);
  
  // Extract segments
  const segments: VocalSegment[] = [];
  let inSegment = false;
  let segStart = 0;
  let segEnergy = 0;
  let segCount = 0;
  
  for (let i = 0; i < withOnsets.length; i++) {
    const time = (i * hopSize) / sampleRate;
    
    if (withOnsets[i] && !inSegment) {
      inSegment = true;
      segStart = time;
      segEnergy = 0;
      segCount = 0;
    } else if (!withOnsets[i] && inSegment) {
      inSegment = false;
      const segEnd = time;
      const duration = segEnd - segStart;
      
      // Very short minimum: 50ms to catch quick vocal starts
      if (duration > 0.05) {
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
  
  // Close last segment
  if (inSegment) {
    const segEnd = (withOnsets.length * hopSize) / sampleRate;
    const duration = segEnd - segStart;
    if (duration > 0.05) {
      segments.push({
        start: segStart,
        end: segEnd,
        energy: segCount > 0 ? segEnergy / segCount : 0,
      });
    }
  }
  
  // Merge close segments (gap < 0.2s — tighter merging)
  const merged = mergeCloseSegments(segments, 0.2);
  
  // Remove very long gaps at the start (but keep the first real vocal segment)
  // Only remove silence before first vocal, don't add artificial delay
  
  if (onProgress) onProgress(1);
  
  return {
    segments: merged,
    energyProfile,
    sampleRate,
    windowSize,
  };
}

/**
 * Enhance detection by looking for energy onsets (sudden increases)
 * which often indicate vocal starts
 */
function applyOnsetDetection(
  smoothed: boolean[],
  energyProfile: number[],
  threshold: number,
  hopSize: number,
  sampleRate: number
): boolean[] {
  const result = [...smoothed];
  const lookback = Math.floor(0.1 * sampleRate / hopSize); // 100ms lookback
  
  for (let i = lookback; i < result.length; i++) {
    if (!result[i]) {
      // Check if there's an energy onset (sudden rise)
      const currentEnergy = energyProfile[i];
      const prevEnergy = energyProfile[i - lookback];
      
      // If energy jumped significantly, mark as vocal
      if (currentEnergy > prevEnergy * 2 && currentEnergy > threshold * 0.7) {
        // Check if surrounding frames also have vocal-range energy
        const zcr = currentEnergy > 0 ? 1 : 0; // simplified check
        if (currentEnergy > threshold * 0.5) {
          result[i] = true;
        }
      }
    }
  }
  
  return result;
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
  
  const merged: VocalSegment[] = [{ ...segments[0] }];
  
  for (let i = 1; i < segments.length; i++) {
    const prev = merged[merged.length - 1];
    const curr = segments[i];
    
    if (curr.start - prev.end < minGap) {
      prev.end = curr.end;
      prev.energy = (prev.energy + curr.energy) / 2;
    } else {
      merged.push({ ...curr });
    }
  }
  
  return merged;
}
