import { useRef, useCallback } from 'react';

interface LyricsInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function LyricsInput({ value, onChange }: LyricsInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        onChange(text);
      };
      reader.readAsText(file);
    }
  }, [onChange]);

  const lineCount = value ? value.split('\n').filter(l => l.trim().length > 0).length : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="block text-gray-300 text-sm font-medium">
          Текст песни
        </label>
        <div className="flex items-center gap-2">
          {lineCount > 0 && (
            <span className="text-gray-500 text-xs">{lineCount} строк</span>
          )}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
          >
            📄 Загрузить TXT
          </button>
        </div>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={"Вставьте текст песни...\n\nПустые строки разделяют части песни.\n\nНапример:\nКуплет 1\nПервая строка...\nВторая строка...\n\nПрипев\nСтрока припева..."}
        className="w-full h-48 bg-gray-800/50 border border-gray-700 rounded-xl p-4 text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors font-mono text-sm leading-relaxed"
      />
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.text,.lrc"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  );
}
