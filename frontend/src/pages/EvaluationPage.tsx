import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { EvaluationMetric } from '../types';
import { Activity, HelpCircle } from 'lucide-react';

const METRIC_EXPLANATIONS: Record<string, string> = {
  recall_at_1: 'How often the correct knowledge source appears as the top retrieved result.',
  recall_at_3: 'How often the correct knowledge source appears within the top 3 retrieved results.',
  recall_at_5: 'How often the correct knowledge source appears within the top 5 retrieved results.',
  mrr: 'Mean Reciprocal Rank — average of 1/rank for correct results. Higher is better.',
  groundedness: 'How well the AI response is supported by the retrieved evidence.',
  citation_accuracy: 'How accurately the AI cites the correct source documents.',
  structured_output_validity: 'How often the AI produces valid structured JSON output.',
  escalation_accuracy: 'How accurately the AI detects issues requiring escalation.',
};

const METRIC_LABELS: Record<string, string> = {
  recall_at_1: 'Recall@1',
  recall_at_3: 'Recall@3',
  recall_at_5: 'Recall@5',
  mrr: 'MRR',
  groundedness: 'Groundedness',
  citation_accuracy: 'Citation Accuracy',
  structured_output_validity: 'Structured Output',
  escalation_accuracy: 'Escalation Accuracy',
};

export default function EvaluationPage() {
  const [metrics, setMetrics] = useState<EvaluationMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);

  useEffect(() => {
    api.getEvaluations().then(m => { setMetrics(m); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const ragMetrics = metrics.filter(m => m.eval_type === 'rag');
  const modelMetrics = metrics.filter(m => m.eval_type === 'model');

  const MetricBar = ({ metric }: { metric: EvaluationMetric }) => {
    const pct = Math.round(metric.metric_value * 100);
    const color = pct >= 85 ? 'bg-green-500' : pct >= 70 ? 'bg-amber-500' : 'bg-red-500';
    return (
      <div
        className="bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-4 hover:shadow-sm transition-shadow relative"
        onMouseEnter={() => setHoveredMetric(metric.metric_name)}
        onMouseLeave={() => setHoveredMetric(null)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-medium text-[var(--text-primary)]">
              {METRIC_LABELS[metric.metric_name] || metric.metric_name}
            </span>
            <HelpCircle className="w-3 h-3 text-[var(--text-tertiary)]" />
          </div>
          <span className="text-lg font-bold text-[var(--text-primary)]">{pct}%</span>
        </div>
        <div className="h-2 bg-[var(--bg-badge)] rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
        </div>
        {hoveredMetric === metric.metric_name && METRIC_EXPLANATIONS[metric.metric_name] && (
          <div className="absolute left-0 right-0 -bottom-1 translate-y-full bg-[var(--bg-surface)] border border-[var(--border)] rounded-lg p-3 shadow-lg z-10">
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              {METRIC_EXPLANATIONS[metric.metric_name]}
            </p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Evaluation Dashboard</h2>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">Model and retrieval performance metrics</p>
      </div>

      {loading ? [...Array(4)].map((_, i) => <div key={i} className="h-20 skeleton rounded-lg" />) : (
        <>
          {ragMetrics.length > 0 && (
            <div>
              <h3 className="text-md font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[var(--text-tertiary)]" />
                RAG Retrieval Performance
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {ragMetrics.map(m => <MetricBar key={m.id} metric={m} />)}
              </div>
            </div>
          )}

          {modelMetrics.length > 0 && (
            <div>
              <h3 className="text-md font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-[var(--text-tertiary)]" />
                Model Quality
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {modelMetrics.map(m => <MetricBar key={m.id} metric={m} />)}
              </div>
            </div>
          )}

          {metrics.length === 0 && (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <Activity className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-md">No evaluation data yet</p>
              <p className="text-sm mt-1">Run evaluation scripts to generate metrics.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
