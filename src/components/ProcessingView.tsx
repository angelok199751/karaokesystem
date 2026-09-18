import { ProcessingStep } from '../lib/types';

interface ProcessingViewProps {
  steps: ProcessingStep[];
}

export function ProcessingView({ steps }: ProcessingViewProps) {
  const completedSteps = steps.filter(s => s.status === 'done').length;
  const totalSteps = steps.length;
  const overallProgress = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <div className="bg-gray-800/50 backdrop-blur rounded-xl p-8 border border-gray-700">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600/20 rounded-full mb-4">
          <div className="w-8 h-8 border-3 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <h2 className="text-xl font-bold text-white mb-1">Обработка</h2>
        <p className="text-gray-400 text-sm">Пожалуйста, подождите...</p>
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">Прогресс</span>
          <span className="text-purple-400 font-medium">{overallProgress}%</span>
        </div>
        <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-600 to-pink-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${overallProgress}%` }}
          ></div>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step) => (
          <StepItem key={step.id} step={step} />
        ))}
      </div>
    </div>
  );
}

function StepItem({ step }: { step: ProcessingStep }) {
  const statusIcon = () => {
    switch (step.status) {
      case 'done':
        return (
          <div className="w-6 h-6 bg-green-500/20 rounded-full flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        );
      case 'active':
        return (
          <div className="w-6 h-6 bg-purple-500/20 rounded-full flex items-center justify-center">
            <div className="w-3 h-3 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
          </div>
        );
      case 'error':
        return (
          <div className="w-6 h-6 bg-red-500/20 rounded-full flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-6 h-6 bg-gray-700 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
          </div>
        );
    }
  };

  const textColor = () => {
    switch (step.status) {
      case 'done': return 'text-green-400';
      case 'active': return 'text-white';
      case 'error': return 'text-red-400';
      default: return 'text-gray-500';
    }
  };

  return (
    <div className="flex items-center gap-3">
      {statusIcon()}
      <span className={`text-sm font-medium ${textColor()}`}>
        {step.label}
      </span>
      {step.status === 'active' && step.progress !== undefined && step.progress > 0 && (
        <span className="text-xs text-purple-400 ml-auto">{step.progress}%</span>
      )}
    </div>
  );
}
