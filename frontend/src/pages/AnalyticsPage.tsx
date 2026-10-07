import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { Analytics } from '../types';
import { BarChart3, MessageSquare, FileCheck, Shield, AlertTriangle, TrendingUp, Edit3, ArrowUpRight } from 'lucide-react';

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalytics().then(a => { setData(a); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 space-y-4">{[...Array(6)].map((_, i) => <div key={i} className="h-28 skeleton rounded-xl" />)}</div>;

  if (!data) return <div className="p-6 text-center text-[var(--text-tertiary)]"><p>Unable to load analytics</p></div>;

  const metrics = [
    { label: 'Total Conversations', value: data.total_conversations, icon: MessageSquare, color: 'text-blue-600' },
    { label: 'AI Drafts', value: data.total_drafts, icon: FileCheck, color: 'text-indigo-600' },
    { label: 'Approval Rate', value: `${data.approval_rate}%`, icon: TrendingUp, color: 'text-green-600' },
    { label: 'Avg Confidence', value: `${data.avg_confidence}%`, icon: Shield, color: 'text-navy-600' },
    { label: 'Escalation Rate', value: `${data.escalation_rate}%`, icon: AlertTriangle, color: 'text-red-600' },
    { label: 'Knowledge Gaps', value: data.knowledge_gap_count, icon: AlertTriangle, color: 'text-amber-600' },
    { label: 'Avg Edit Distance', value: `${(data.avg_edit_distance * 100).toFixed(1)}%`, icon: Edit3, color: 'text-teal-600' },
    { label: 'Rejection Rate', value: `${data.rejection_rate}%`, icon: ArrowUpRight, color: 'text-orange-600' },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Analytics</h2>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">Real metrics from your support operations</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {metrics.map(m => (
          <div key={m.label} className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-4">
            <div className="flex items-center gap-2 mb-2">
              <m.icon className={`w-4 h-4 ${m.color}`} />
              <span className="text-xs text-[var(--text-tertiary)]">{m.label}</span>
            </div>
            <p className="text-xl font-bold text-[var(--text-primary)]">{m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* By Category */}
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
          <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4">By Category</h3>
          {Object.entries(data.conversations_by_category).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(data.conversations_by_category).map(([cat, count]) => {
                const total = data.total_conversations || 1;
                return (
                  <div key={cat}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[var(--text-secondary)]">{cat}</span>
                      <span className="text-[var(--text-tertiary)]">{count}</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-badge)] rounded-full overflow-hidden">
                      <div className="h-full bg-navy-500 rounded-full" style={{ width: `${(count / total) * 100}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : <p className="text-sm text-[var(--text-tertiary)]">No category data</p>}
        </div>

        {/* By Priority */}
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
          <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4">By Priority</h3>
          {Object.entries(data.conversations_by_priority).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(data.conversations_by_priority).map(([pri, count]) => {
                const colors: Record<string, string> = { urgent: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-blue-500', low: 'bg-gray-400' };
                const total = data.total_conversations || 1;
                return (
                  <div key={pri}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[var(--text-secondary)] capitalize">{pri}</span>
                      <span className="text-[var(--text-tertiary)]">{count}</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-badge)] rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${colors[pri] || 'bg-gray-400'}`} style={{ width: `${(count / total) * 100}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : <p className="text-sm text-[var(--text-tertiary)]">No priority data</p>}
        </div>
      </div>
    </div>
  );
}
