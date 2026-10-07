import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { Analytics, SystemHealth } from '../types';
import { MessageSquare, FileCheck, TrendingUp, AlertTriangle, Shield, Activity, CheckCircle, XCircle } from 'lucide-react';

function MetricCard({ label, value, sub, icon: Icon, color }: {
  label: string; value: string | number; sub?: string; icon: any; color: string;
}) {
  return (
    <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--text-tertiary)] mb-1">{label}</p>
          <p className="text-2xl font-bold text-[var(--text-primary)]">{value}</p>
          {sub && <p className="text-xs text-[var(--text-tertiary)] mt-1">{sub}</p>}
        </div>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const ok = ['connected', 'ready', 'loaded'].includes(status);
  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${ok ? 'bg-green-500' : 'bg-amber-500'}`} />
      <span className="text-sm text-[var(--text-secondary)] capitalize">{status.replace(/_/g, ' ')}</span>
    </div>
  );
}

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAnalytics().catch(() => null),
      api.getSystemHealth().catch(() => null),
    ]).then(([a, h]) => {
      setAnalytics(a);
      setHealth(h);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 skeleton rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">Support Overview</h2>
        <p className="text-sm text-[var(--text-tertiary)] mt-0.5">AI assists. Humans decide.</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Conversations"
          value={analytics?.total_conversations ?? 0}
          icon={MessageSquare}
          color="bg-navy-50 text-navy-600 dark:bg-navy-950 dark:text-navy-400"
        />
        <MetricCard
          label="AI Drafts Generated"
          value={analytics?.total_drafts ?? 0}
          sub={`${analytics?.approval_rate ?? 0}% approval rate`}
          icon={FileCheck}
          color="bg-teal-50 text-teal-600 dark:bg-teal-950 dark:text-teal-400"
        />
        <MetricCard
          label="Avg Confidence"
          value={`${analytics?.avg_confidence ?? 0}%`}
          icon={TrendingUp}
          color="bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
        />
        <MetricCard
          label="Knowledge Gaps"
          value={analytics?.knowledge_gap_count ?? 0}
          sub={`${analytics?.escalation_rate ?? 0}% escalation rate`}
          icon={AlertTriangle}
          color="bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400"
        />
      </div>

      {/* Two column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* System Health */}
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
          <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Activity className="w-4 h-4 text-[var(--text-tertiary)]" />
            System Status
          </h3>
          {health ? (
            <div className="space-y-3">
              <div className="flex justify-between"><span className="text-sm text-[var(--text-secondary)]">Database</span><StatusDot status={health.database} /></div>
              <div className="flex justify-between"><span className="text-sm text-[var(--text-secondary)]">RAG Index</span><StatusDot status={health.rag_index} /></div>
              <div className="flex justify-between"><span className="text-sm text-[var(--text-secondary)]">Embedding Model</span><StatusDot status={health.embedding_model} /></div>
              <div className="flex justify-between"><span className="text-sm text-[var(--text-secondary)]">LLM</span><StatusDot status={health.llm} /></div>
              <div className="flex justify-between"><span className="text-sm text-[var(--text-secondary)]">Model Adapter</span><StatusDot status={health.model_adapter} /></div>
            </div>
          ) : (
            <p className="text-sm text-[var(--text-tertiary)]">Unable to check system status</p>
          )}
        </div>

        {/* Confidence Distribution */}
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
          <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-[var(--text-tertiary)]" />
            Grounding Confidence
          </h3>
          {analytics?.confidence_distribution ? (
            <div className="space-y-3">
              {['high', 'medium', 'low'].map(level => {
                const count = analytics.confidence_distribution[level] ?? 0;
                const total = Object.values(analytics.confidence_distribution).reduce((a, b) => a + b, 0);
                const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                const colors = { high: 'bg-green-500', medium: 'bg-amber-500', low: 'bg-red-500' };
                return (
                  <div key={level}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-[var(--text-secondary)] capitalize">{level}</span>
                      <span className="text-[var(--text-tertiary)]">{count} drafts ({pct}%)</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-badge)] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${colors[level as keyof typeof colors]}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-tertiary)]">No draft data yet</p>
          )}
        </div>
      </div>

      {/* Quick Stats */}
      {analytics && (
        <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
          <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4">Conversations by Status</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(analytics.conversations_by_status).map(([status, count]) => (
              <div key={status} className="px-3 py-2 rounded-lg bg-[var(--bg-badge)] text-sm">
                <span className="text-[var(--text-secondary)] capitalize">{status.replace(/_/g, ' ')}</span>
                <span className="ml-2 font-semibold text-[var(--text-primary)]">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
