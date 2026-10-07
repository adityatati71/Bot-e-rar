import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { KnowledgeGap } from '../types';
import { AlertTriangle, TrendingUp, BookOpen } from 'lucide-react';

const IMPACT_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
};

export default function GapsPage() {
  const [gaps, setGaps] = useState<KnowledgeGap[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getKnowledgeGaps().then(g => { setGaps(g); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const openGaps = gaps.filter(g => g.status === 'open');
  const highImpact = gaps.filter(g => g.impact === 'high');

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Knowledge Gaps</h2>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">Topics where the knowledge base needs improvement</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-tertiary)] mb-2">
            <AlertTriangle className="w-4 h-4" /><span className="text-xs font-medium">Open Gaps</span>
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{openGaps.length}</p>
        </div>
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-tertiary)] mb-2">
            <TrendingUp className="w-4 h-4" /><span className="text-xs font-medium">High Impact</span>
          </div>
          <p className="text-2xl font-bold text-red-600">{highImpact.length}</p>
        </div>
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-4">
          <div className="flex items-center gap-2 text-[var(--text-tertiary)] mb-2">
            <BookOpen className="w-4 h-4" /><span className="text-xs font-medium">Total Detected</span>
          </div>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{gaps.length}</p>
        </div>
      </div>

      {/* Gap list */}
      {loading ? [...Array(3)].map((_, i) => <div key={i} className="h-32 skeleton rounded-xl" />) :
        gaps.length === 0 ? (
          <div className="text-center py-16 text-[var(--text-tertiary)]">
            <AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p className="text-md">No knowledge gaps detected</p>
            <p className="text-sm mt-1">Bot-ए-rar has not identified any unresolved support topics yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {gaps.map(gap => (
              <div key={gap.id} className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-md font-semibold text-[var(--text-primary)]">{gap.topic}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${IMPACT_COLORS[gap.impact] || ''}`}>{gap.impact} impact</span>
                      <span className="text-xs text-[var(--text-tertiary)]">Asked {gap.frequency}x</span>
                      <span className={`text-xs ${gap.status === 'open' ? 'text-amber-600' : 'text-green-600'}`}>{gap.status}</span>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-[var(--text-secondary)] mt-2 leading-relaxed">{gap.description}</p>
                {gap.question_pattern && (
                  <p className="text-xs text-[var(--text-tertiary)] mt-2 italic">Example: "{gap.question_pattern}"</p>
                )}
                {gap.recommended_action && (
                  <div className="mt-3 p-2 rounded-lg bg-[var(--bg-badge)] text-xs text-[var(--text-secondary)]">
                    <span className="font-medium">Recommended: </span>{gap.recommended_action}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      }
    </div>
  );
}
