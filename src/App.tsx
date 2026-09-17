import { useState, useCallback } from 'react';
import { AudioInfo, AppState, ProcessingStep } from './lib/types';
import { decodeAudio } from './lib/audioDecoder';
import { processKaraoke, ProcessingResult } from './lib/processor';
import { AudioInput } from './components/AudioInput';
import { LyricsInput } from './components/LyricsInput';
import { TitleInput } from './components/TitleInput';
import { ProcessingView } from './components/ProcessingView';
import { ResultView } from './components/ResultView';
import { ErrorView } from './components/ErrorView';

function App() {
  const [appState, setAppState] = useState<AppState>('input');
  const [audioInfo, setAudioInfo] = useState<AudioInfo | null>(null);
  const [lyrics, setLyrics] = useState('');
  const [title, setTitle] = useState('');
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [result, setResult] = useState<ProcessingResult | null>(null);
  const [error, setError] = useState<string>('');

  const handleAudioLoaded = useCallback(async (file: File) => {
    try {
      const info = await decodeAudio(file);
      setAudioInfo(info);
    } catch (err) {
      setError('Не удалось прочитать аудиофайл. Попробуйте другой файл.');
      setAppState('error');
    }
  }, []);

  const handleAudioRemove = useCallback(() => {
    setAudioInfo(null);
  }, []);

  const handleCreate = useCallback(async () => {
    if (!audioInfo || !lyrics.trim() || !title.trim()) return;

    setAppState('processing');
    setError('');

    try {
      const processingResult = await processKaraoke(
        audioInfo,
        lyrics,
        title,
        (steps) => setProcessingSteps([...steps])
      );
      
      setResult(processingResult);
      setAppState('result');
    } catch (err) {
      console.error('Processing error:', err);
      setError('Не удалось создать караоке. Проверьте качество аудиозаписи и текст песни.');
      setAppState('error');
    }
  }, [audioInfo, lyrics, title]);

  const handleReset = useCallback(() => {
    setAppState('input');
    setAudioInfo(null);
    setLyrics('');
    setTitle('');
    setProcessingSteps([]);
    setResult(null);
    setError('');
  }, []);

  const canCreate = audioInfo !== null && lyrics.trim().length > 0 && title.trim().length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Header */}
        <header className="text-center mb-10">
          <h1 className="text-4xl font-bold text-white mb-2">
            🎤 КАРАОКЕ БИЛДЕР
          </h1>
          <p className="text-gray-400 text-sm">
            Создайте караоке-файл из песни и текста
          </p>
        </header>

        {/* Main Content */}
        {appState === 'input' && (
          <div className="space-y-6">
            {/* Step 1: Title */}
            <TitleInput value={title} onChange={setTitle} />

            {/* Step 2: Audio */}
            <AudioInput 
              audioInfo={audioInfo} 
              onLoaded={handleAudioLoaded}
              onRemove={handleAudioRemove}
            />

            {/* Step 3: Lyrics */}
            <LyricsInput value={lyrics} onChange={setLyrics} />

            {/* Create Button */}
            <div className="pt-4">
              <button
                onClick={handleCreate}
                disabled={!canCreate}
                className={`w-full py-4 px-6 rounded-xl text-lg font-bold transition-all duration-200 ${
                  canCreate
                    ? 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 hover:shadow-purple-500/40 active:scale-[0.98]'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                СОЗДАТЬ КАРАОКЕ
              </button>
              {!canCreate && (
                <p className="text-center text-gray-500 text-sm mt-2">
                  Заполните все поля для начала обработки
                </p>
              )}
            </div>
          </div>
        )}

        {appState === 'processing' && (
          <ProcessingView steps={processingSteps} />
        )}

        {appState === 'result' && result && audioInfo && (
          <ResultView
            title={title}
            duration={audioInfo.duration}
            lyrics={result.lyrics}
            karaokeBlob={result.karaokeBlob}
            audioFile={audioInfo.file}
            onReset={handleReset}
          />
        )}

        {appState === 'error' && (
          <ErrorView message={error} onReset={handleReset} />
        )}
      </div>
    </div>
  );
}

export default App;
