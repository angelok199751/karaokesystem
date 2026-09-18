interface ErrorViewProps {
  message: string;
  onReset: () => void;
}

export function ErrorView({ message, onReset }: ErrorViewProps) {
  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl p-8 border border-red-900/50 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-4">
        <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Ошибка</h2>
      <p className="text-gray-300 mb-6">{message}</p>
      <button
        onClick={onReset}
        className="py-3 px-6 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-xl font-medium transition-colors"
      >
        Попробовать снова
      </button>
    </div>
  );
}
