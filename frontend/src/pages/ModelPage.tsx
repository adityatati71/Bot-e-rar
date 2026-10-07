import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { ModelInsights } from '../types';
import { Brain, Cpu, Database, Layers, Gauge, Code } from 'lucide-react';

export default function ModelPage() {
  const [model, setModel] = useState<ModelInsights | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getModelInsights().then(m => { setModel(m); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-32 skeleton rounded-xl" />)}</div>;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Model Insights</h2>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">Current model configuration and performance</p>
      </div>

      {model && model.current_model ? (
        <>
          {/* Model Card */}
          <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-navy-50 dark:bg-navy-950">
                <Brain className="w-6 h-6 text-navy-600 dark:text-navy-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">{model.current_model}</h3>
                <p className="text-sm text-[var(--text-tertiary)] mt-0.5">Bot-ए-rar Support Model</p>
              </div>
              {model.is_active && (
                <span className="ml-auto px-2.5 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-medium">
                  Active
                </span>
              )}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InfoCard icon={Cpu} label="Base Model" value={model.base_model} />
            <InfoCard icon={Layers} label="Fine-tuning Method" value={model.fine_tuning_method || 'N/A'} />
            <InfoCard icon={Database} label="Training Dataset" value={model.training_dataset_size ? `${model.training_dataset_size.toLocaleString()} examples` : 'N/A'} />
            <InfoCard icon={Gauge} label="Validation Loss" value={model.validation_loss?.toFixed(4) || 'N/A'} />
            <InfoCard icon={Code} label="Quantization" value={model.quantization || 'None'} />
            <InfoCard icon={Layers} label="Context Size" value={model.context_size ? `${model.context_size.toLocaleString()} tokens` : 'N/A'} />
          </div>

          {/* Eval Metrics */}
          {Object.keys(model.eval_metrics).length > 0 && (
            <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
              <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4">Evaluation Metrics</h3>
              <div className="space-y-3">
                {Object.entries(model.eval_metrics).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[var(--text-secondary)] capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-[var(--text-primary)]">{(val * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-badge)] rounded-full overflow-hidden">
                      <div className="h-full bg-navy-500 rounded-full" style={{ width: `${val * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-16 text-[var(--text-tertiary)]">
          <Brain className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-md">No model configured</p>
          <p className="text-sm mt-1">Run the training pipeline to create a model version.</p>
        </div>
      )}
    </div>
  );
}

function InfoCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-[var(--text-tertiary)]" />
        <span className="text-xs text-[var(--text-tertiary)]">{label}</span>
      </div>
      <p className="text-md font-medium text-[var(--text-primary)]">{value}</p>
    </div>
  );
}
