interface TitleInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function TitleInput({ value, onChange }: TitleInputProps) {
  return (
    <div>
      <label className="block text-gray-300 text-sm font-medium mb-2">
        Название песни
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Например: Король и Шут — Лесник"
        className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors"
      />
    </div>
  );
}
