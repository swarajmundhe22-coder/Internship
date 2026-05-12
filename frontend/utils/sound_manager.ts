/**
 * Enterprise-grade Sound Design Manager for The On Looker.
 * Engineered for low-latency spatial audio and multi-sensory immersion.
 */
class SoundManager {
  private static instance: SoundManager;
  private audioContext: AudioContext | null = null;
  private gainNode: GainNode | null = null;
  private buffers: Map<string, AudioBuffer> = new Map();

  private constructor() {
    if (typeof window !== "undefined") {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.gainNode = this.audioContext.createGain();
      this.gainNode.connect(this.audioContext.destination);
    }
  }

  public static getInstance(): SoundManager {
    if (!SoundManager.instance) {
      SoundManager.instance = new SoundManager();
    }
    return SoundManager.instance;
  }

  /**
   * Preload audio assets into memory for sub-millisecond playback latency.
   */
  public async loadSound(name: string, url: string): Promise<void> {
    if (!this.audioContext) return;
    try {
      const response = await fetch(url);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      this.buffers.set(name, audioBuffer);
    } catch (err) {
      console.error(`Failed to load sound ${name}:`, err);
    }
  }

  /**
   * Play a sound with optional spatial panning and emotionally tuned volume.
   */
  public playSound(name: string, volume: number = 0.5, pan: number = 0): void {
    if (!this.audioContext || !this.gainNode) return;
    
    const buffer = this.buffers.get(name);
    if (!buffer) return;

    // Ensure context is running (user interaction might be required)
    if (this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }

    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;

    const panner = this.audioContext.createPanner();
    panner.setPosition(pan, 0, 1 - Math.abs(pan));

    const localGain = this.audioContext.createGain();
    localGain.gain.value = volume;

    source.connect(localGain);
    localGain.connect(panner);
    panner.connect(this.gainNode);

    source.start(0);
  }

  public setGlobalVolume(volume: number): void {
    if (this.gainNode) {
      this.gainNode.gain.setTargetAtTime(volume, this.audioContext?.currentTime || 0, 0.1);
    }
  }
}

export const soundManager = SoundManager.getInstance();
