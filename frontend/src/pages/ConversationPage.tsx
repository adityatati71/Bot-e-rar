import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useStore } from '../stores/useStore';
import type { ConversationDetail, DraftResponse, CitationItem } from '../types';
import {
  ArrowLeft, Sparkles, Check, X, RefreshCw, AlertTriangle,
  Shield, Clock, FileText, ChevronDown, ChevronUp, User, Bot,
  Send, Edit3, ExternalLink, Loader2,
} from 'lucide-react';

// ── Generation steps animation ────────────────────────────
const GEN_STEPS = [
  'Analyzing conversation',
  'Searching knowledge base',
  'Checking evidence',
  'Drafting response',
];

function GeneratingOverlay({ step }: { step: number }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-6 h-6 text-navy-500 animate-spin mb-4" />
      <div className="space-y-2">
        {GEN_STEPS.map((s, i) => (
          <div key={i} className={`flex items-center gap-2 text-sm transition-colors ${
            i < step ? 'text-green-600' : i === step ? 'text-navy-600 font-medium' : 'text-[var(--text-tertiary)]'
          }`}>
            {i < step ? <Check className="w-3.5 h-3.5" /> :
              i === step ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
              <div className="w-3.5 h-3.5 rounded-full border border-[var(--border)]" />}
            {s}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Confidence Meter ──────────────────────────────────────
function ConfidenceMeter({ confidence }: { confidence: DraftResponse['confidence'] }) {
  const levelColors = { high: 'text-green-600', medium: 'text-amber-600', low: 'text-red-600' };
  const barColors = { high: 'bg-green-500', medium: 'bg-amber-500', low: 'bg-red-500' };
  const levelLabels = { high: 'Strong', medium: 'Moderate', low: 'Weak' };

  const details = [
    { label: 'Retrieval relevance', value: confidence.retrieval_relevance ?? 0 },
    { label: 'Source coverage', value: confidence.source_coverage ?? 0 },
    { label: 'Freshness', value: confidence.freshness ?? 0 },
    { label: 'Consistency', value: confidence.consistency ?? 0 },
  ];

  return (
    <div className="bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-[var(--text-secondary)]">Grounding Confidence</span>
        <div className="flex items-center gap-1.5">
          <span className={`text-lg font-bold ${levelColors[confidence.level as keyof typeof levelColors] || ''}`}>
            {Math.round(confidence.score)}%
          </span>
          <span className={`text-xs font-medium ${levelColors[confidence.level as keyof typeof levelColors] || ''}`}>
            {levelLabels[confidence.level as keyof typeof levelLabels] || confidence.level}
          </span>
        </div>
      </div>
      <div className="space-y-2">
        {details.map(d => (
          <div key={d.label}>
            <div className="flex justify-between text-xs text-[var(--text-tertiary)] mb-0.5">
              <span>{d.label}</span>
              <span>{Math.round(d.value)}%</span>
            </div>
            <div className="h-1.5 bg-[var(--bg-badge)] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${barColors[confidence.level as keyof typeof barColors] || 'bg-gray-400'}`}
                style={{ width: `${d.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>
      {confidence.reasons.length > 0 && (
        <div className="mt-3 pt-3 border-t border-[var(--border)] space-y-1">
          {confidence.reasons.map((r, i) => (
            <p key={i} className="text-xs text-[var(--text-tertiary)]">• {r}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Citation Card ─────────────────────────────────────────
function CitationCard({ citation, index }: { citation: CitationItem; index: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-3 hover:border-[var(--border-strong)] transition-colors">
      <button onClick={() => setExpanded(!expanded)} className="w-full text-left">
        <div className="flex items-start gap-2">
          <span className="flex items-center justify-center w-5 h-5 rounded bg-navy-100 dark:bg-navy-900 text-navy-700 dark:text-navy-300 text-[10px] font-bold shrink-0">
            {index + 1}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[var(--text-primary)] truncate">{citation.title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              {citation.version && <span className="text-xs text-[var(--text-tertiary)]">v{citation.version}</span>}
              {citation.updated_at && <span className="text-xs text-[var(--text-tertiary)]">Updated {citation.updated_at}</span>}
              <span className="text-xs text-[var(--text-tertiary)]">{Math.round(citation.relevance_score * 100)}% relevant</span>
            </div>
          </div>
          {expanded ? <ChevronUp className="w-3.5 h-3.5 text-[var(--text-tertiary)] shrink-0" /> :
                      <ChevronDown className="w-3.5 h-3.5 text-[var(--text-tertiary)] shrink-0" />}
        </div>
      </button>
      {expanded && (
        <div className="mt-2 pl-7">
          <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-badge)] rounded p-2">
            "{citation.snippet}"
          </p>
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────
export default function ConversationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const addToast = useStore(s => s.addToast);

  const [conv, setConv] = useState<ConversationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genStep, setGenStep] = useState(0);
  const [editedReply, setEditedReply] = useState('');
  const [editing, setEditing] = useState(false);
  const [approving, setApproving] = useState(false);
  const [showConfirmApprove, setShowConfirmApprove] = useState(false);

  const latestDraft = conv?.drafts?.[0];

  useEffect(() => {
    if (id) {
      api.getConversation(id).then(c => {
        setConv(c);
        if (c.drafts?.[0]) setEditedReply(c.drafts[0].draft_reply);
        setLoading(false);
      }).catch(() => setLoading(false));
    }
  }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setGenerating(true);
    setGenStep(0);

    // Simulate step progression
    const stepInterval = setInterval(() => {
      setGenStep(s => Math.min(s + 1, GEN_STEPS.length - 1));
    }, 800);

    try {
      const draft = await api.generateDraft(id);
      clearInterval(stepInterval);
      setConv(prev => prev ? { ...prev, drafts: [draft, ...(prev.drafts || [])], status: 'ai_drafted' } : prev);
      setEditedReply(draft.draft_reply);
      addToast({ message: 'Draft ready', type: 'success' });
    } catch (err: any) {
      addToast({ message: err.message || 'Failed to generate draft', type: 'error' });
    } finally {
      clearInterval(stepInterval);
      setGenerating(false);
    }
  };

  const handleApprove = async () => {
    if (!latestDraft) return;
    setApproving(true);
    try {
      const finalReply = editing ? editedReply : undefined;
      await api.approveDraft(latestDraft.id, finalReply);
      addToast({ message: 'Response approved', type: 'success' });
      setShowConfirmApprove(false);
      // Refresh
      const c = await api.getConversation(id!);
      setConv(c);
    } catch (err: any) {
      addToast({ message: err.message || 'Approval failed', type: 'error' });
    } finally {
      setApproving(false);
    }
  };

  const handleRegenerate = async () => {
    if (!latestDraft) return;
    setGenerating(true);
    setGenStep(0);
    const stepInterval = setInterval(() => setGenStep(s => Math.min(s + 1, 3)), 800);
    try {
      const draft = await api.regenerateDraft(latestDraft.id);
      clearInterval(stepInterval);
      setConv(prev => prev ? { ...prev, drafts: [draft, ...(prev.drafts || [])] } : prev);
      setEditedReply(draft.draft_reply);
      setEditing(false);
      addToast({ message: 'Response regenerated', type: 'success' });
    } catch (err: any) {
      addToast({ message: err.message, type: 'error' });
    } finally {
      clearInterval(stepInterval);
      setGenerating(false);
    }
  };

  const handleEscalate = async () => {
    if (!latestDraft) return;
    try {
      await api.escalateDraft(latestDraft.id);
      addToast({ message: 'Escalation created', type: 'info' });
      const c = await api.getConversation(id!);
      setConv(c);
    } catch (err: any) {
      addToast({ message: err.message, type: 'error' });
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-48 skeleton rounded" />
        <div className="h-64 skeleton rounded-xl" />
      </div>
    );
  }

  if (!conv) {
    return (
      <div className="p-6 text-center text-[var(--text-tertiary)]">
        <p className="text-md">Conversation not found</p>
        <button onClick={() => navigate('/inbox')} className="mt-2 text-navy-600 text-sm hover:underline">Back to inbox</button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-surface)] shrink-0">
        <button onClick={() => navigate('/inbox')} className="p-1 rounded hover:bg-[var(--bg-surface-hover)] transition-colors">
          <ArrowLeft className="w-4 h-4 text-[var(--text-secondary)]" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-md font-semibold text-[var(--text-primary)] truncate">{conv.subject}</h2>
          <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
            <span>{conv.customer_name}</span>
            {conv.customer_company && <><span>•</span><span>{conv.customer_company}</span></>}
            {conv.category && <><span>•</span><span>{conv.category}</span></>}
          </div>
        </div>
        {!latestDraft && !generating && (
          <button
            onClick={handleGenerate}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Generate AI Draft
          </button>
        )}
      </div>

      {/* Three-column workspace */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* LEFT: Conversation */}
        <div className="w-1/3 min-w-[280px] border-r border-[var(--border)] flex flex-col overflow-hidden">
          <div className="px-4 py-2 border-b border-[var(--border)] bg-[var(--bg-surface)]">
            <span className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">Conversation</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {conv.messages.map(msg => (
              <div key={msg.id} className={`flex gap-2 ${msg.sender === 'customer' ? '' : 'flex-row-reverse'}`}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                  msg.sender === 'customer' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                  'bg-navy-100 text-navy-700 dark:bg-navy-900/30 dark:text-navy-400'
                }`}>
                  {msg.sender === 'customer' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                </div>
                <div className={`max-w-[85%] rounded-lg px-3 py-2 ${
                  msg.sender === 'customer'
                    ? 'bg-[var(--bg-badge)] text-[var(--text-primary)]'
                    : 'bg-navy-50 dark:bg-navy-950 text-[var(--text-primary)]'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  <p className="text-[10px] text-[var(--text-tertiary)] mt-1 capitalize">{msg.sender}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CENTER: AI Draft */}
        <div className="flex-1 min-w-[320px] flex flex-col overflow-hidden">
          <div className="px-4 py-2 border-b border-[var(--border)] bg-[var(--bg-surface)]">
            <span className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">AI Draft</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {generating ? (
              <GeneratingOverlay step={genStep} />
            ) : latestDraft ? (
              <div className="space-y-4">
                {/* Escalation banner */}
                {latestDraft.escalation.required && (
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                    <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-red-700 dark:text-red-400">Security Review Required</p>
                      <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">{latestDraft.escalation.reason}</p>
                      {latestDraft.escalation.recommended_team && (
                        <p className="text-xs text-red-500 mt-1">Recommended: {latestDraft.escalation.recommended_team}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Knowledge gap banner */}
                {latestDraft.knowledge_gap.needed && (
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-700 dark:text-amber-400">Knowledge Gap Detected</p>
                      <p className="text-xs text-amber-600 dark:text-amber-400 mt-0.5">{latestDraft.knowledge_gap.reason}</p>
                    </div>
                  </div>
                )}

                {/* Summary */}
                {latestDraft.short_summary && (
                  <div className="px-3 py-2 rounded-lg bg-[var(--bg-badge)] text-xs text-[var(--text-secondary)]">
                    {latestDraft.short_summary}
                  </div>
                )}

                {/* Draft text */}
                <div className="bg-[var(--bg-surface)] rounded-lg border border-[var(--border)] p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs text-[var(--text-tertiary)]">
                      Generated from {latestDraft.citations.length} verified source{latestDraft.citations.length !== 1 ? 's' : ''}
                    </span>
                    {!editing && latestDraft.status !== 'approved' && (
                      <button
                        onClick={() => setEditing(true)}
                        className="flex items-center gap-1 text-xs text-navy-600 hover:text-navy-700 transition-colors"
                      >
                        <Edit3 className="w-3 h-3" />
                        Edit Draft
                      </button>
                    )}
                  </div>

                  {editing ? (
                    <textarea
                      value={editedReply}
                      onChange={e => setEditedReply(e.target.value)}
                      rows={10}
                      className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] leading-relaxed focus:outline-none focus:ring-2 focus:ring-navy-500/30 resize-y"
                    />
                  ) : (
                    <div className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-wrap">
                      {latestDraft.edited_reply || latestDraft.draft_reply}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {latestDraft.status !== 'approved' && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowConfirmApprove(true)}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Approve
                    </button>
                    <button
                      onClick={handleRegenerate}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] transition-colors"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Regenerate
                    </button>
                    {latestDraft.escalation.required && (
                      <button
                        onClick={handleEscalate}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-red-300 dark:border-red-800 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                      >
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Escalate
                      </button>
                    )}
                  </div>
                )}

                {latestDraft.status === 'approved' && (
                  <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                    <Check className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-700 dark:text-green-400">Response Approved</span>
                    {latestDraft.edit_distance != null && latestDraft.edit_distance > 0 && (
                      <span className="text-xs text-green-600 dark:text-green-400">
                        • Human edited {Math.round(latestDraft.edit_distance * 100)}% of generated response
                      </span>
                    )}
                  </div>
                )}

                {/* Latency info */}
                {latestDraft.total_latency_ms && (
                  <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Total: {Math.round(latestDraft.total_latency_ms)}ms</span>
                    {latestDraft.retrieval_latency_ms && <span>Retrieval: {Math.round(latestDraft.retrieval_latency_ms)}ms</span>}
                    {latestDraft.generation_latency_ms && <span>Generation: {Math.round(latestDraft.generation_latency_ms)}ms</span>}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-[var(--text-tertiary)]">
                <Sparkles className="w-8 h-8 mb-3 opacity-30" />
                <p className="text-md">No draft generated yet</p>
                <p className="text-sm mt-1">Click "Generate AI Draft" to analyze the conversation</p>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Evidence */}
        <div className="w-1/3 min-w-[260px] border-l border-[var(--border)] flex flex-col overflow-hidden">
          <div className="px-4 py-2 border-b border-[var(--border)] bg-[var(--bg-surface)]">
            <span className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider">Evidence & Knowledge</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {latestDraft ? (
              <>
                <ConfidenceMeter confidence={latestDraft.confidence} />

                {/* Citations */}
                {latestDraft.citations.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Sources</h4>
                    <div className="space-y-2">
                      {latestDraft.citations.map((c, i) => (
                        <CitationCard key={i} citation={c} index={i} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Knowledge gap detail */}
                {latestDraft.knowledge_gap.needed && (
                  <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800 p-4">
                    <h4 className="text-sm font-medium text-amber-700 dark:text-amber-400 mb-2">Knowledge Gap</h4>
                    <p className="text-xs text-amber-600 dark:text-amber-400 leading-relaxed">{latestDraft.knowledge_gap.reason}</p>
                    {latestDraft.knowledge_gap.missing_topic && (
                      <p className="text-xs text-amber-500 mt-2">Topic: {latestDraft.knowledge_gap.missing_topic}</p>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-[var(--text-tertiary)]">
                <FileText className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p className="text-sm">Evidence will appear here after generating a draft</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Approve confirmation modal */}
      {showConfirmApprove && latestDraft && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[var(--z-modal)]" onClick={() => setShowConfirmApprove(false)}>
          <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-6 max-w-sm w-full mx-4 shadow-xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-md font-semibold text-[var(--text-primary)] mb-3">Approve this response?</h3>
            <div className="space-y-2 mb-4 text-sm text-[var(--text-secondary)]">
              <p>• {latestDraft.citations.length} sources verified</p>
              <p>• {Math.round(latestDraft.confidence.score)}% grounding confidence</p>
              <p>• {latestDraft.escalation.required ? 'Escalation required' : 'No escalation required'}</p>
              {editing && <p>• Response was edited by human</p>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowConfirmApprove(false)}
                className="flex-1 px-3 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex-1 px-3 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors disabled:opacity-50"
              >
                {approving ? 'Approving...' : 'Approve Response'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
