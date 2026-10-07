import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { useStore } from '../stores/useStore';
import type { ConversationListItem } from '../types';
import { Search, Clock, Shield, MessageSquare, ArrowRight, Plus, X, Send } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  open: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  ai_drafted: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  human_review: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  sent: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  escalated: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  closed: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
};

const PRIORITY_COLORS: Record<string, string> = {
  urgent: 'text-red-600',
  high: 'text-orange-600',
  medium: 'text-blue-600',
  low: 'text-gray-500',
};

function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function InboxPage() {
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [showNewModal, setShowNewModal] = useState(false);
  const navigate = useNavigate();
  const { addToast, activeOrgId, organizations } = useStore();

  const loadConversations = () => {
    setLoading(true);
    const params = activeOrgId ? { organization_id: activeOrgId } : undefined;
    api.getConversations(params).then(c => {
      setConversations(c);
      setLoading(false);
    }).catch(() => setLoading(false));
  };

  useEffect(() => { loadConversations(); }, [activeOrgId]);

  const filtered = conversations.filter(c => {
    if (search && !c.subject.toLowerCase().includes(search.toLowerCase()) &&
        !c.customer_name.toLowerCase().includes(search.toLowerCase())) return false;
    if (filter !== 'all' && c.status !== filter) return false;
    return true;
  });

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Support Inbox</h2>
          <p className="text-sm text-[var(--text-tertiary)]">{conversations.length} conversations</p>
        </div>
        <button
          onClick={() => setShowNewModal(true)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Conversation
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30 focus:border-navy-500 transition"
          />
        </div>
        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30"
        >
          <option value="all">All Status</option>
          <option value="new">New</option>
          <option value="ai_drafted">AI Drafted</option>
          <option value="human_review">Under Review</option>
          <option value="approved">Approved</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <div key={i} className="h-24 skeleton rounded-xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-[var(--text-tertiary)]">
          <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-md">No conversations found</p>
          <p className="text-sm mt-1">Click "New Conversation" to create one and test the AI copilot.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map(conv => (
            <button
              key={conv.id}
              onClick={() => navigate(`/conversation/${conv.id}`)}
              className="w-full text-left bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-4 hover:shadow-sm hover:border-[var(--border-strong)] transition-all group"
            >
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-md text-[var(--text-primary)]">{conv.customer_company || conv.customer_name}</span>
                    <span className={`text-xs font-medium ${PRIORITY_COLORS[conv.priority] || ''}`}>
                      {conv.priority === 'urgent' && '●'} {conv.priority}
                    </span>
                  </div>
                  <p className="text-sm text-[var(--text-primary)] truncate">{conv.subject}</p>
                  {conv.latest_message && (
                    <p className="text-xs text-[var(--text-tertiary)] mt-1 truncate">{conv.latest_message}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2">
                    <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium ${STATUS_COLORS[conv.status] || STATUS_COLORS.new}`}>
                      {conv.status.replace(/_/g, ' ')}
                    </span>
                    {conv.category && (
                      <span className="text-xs text-[var(--text-tertiary)]">{conv.category}</span>
                    )}
                    {conv.draft_confidence != null && (
                      <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        {Math.round(conv.draft_confidence)}% grounded
                      </span>
                    )}
                    {conv.source_count != null && (
                      <span className="text-xs text-[var(--text-tertiary)]">
                        {conv.source_count} sources
                      </span>
                    )}
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs text-[var(--text-tertiary)] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {timeAgo(conv.created_at)}
                  </span>
                  <ArrowRight className="w-4 h-4 text-[var(--text-tertiary)] mt-3 opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* ── New Conversation Modal ──────────────────────────── */}
      {showNewModal && (
        <NewConversationModal
          onClose={() => setShowNewModal(false)}
          onCreated={(id) => {
            setShowNewModal(false);
            loadConversations();
            navigate(`/conversation/${id}`);
            addToast({ message: 'Conversation created — generate an AI draft!', type: 'success' });
          }}
        />
      )}
    </div>
  );
}


function NewConversationModal({ onClose, onCreated }: {
  onClose: () => void;
  onCreated: (id: string) => void;
}) {
  const { activeOrgId } = useStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('General');
  const [priority, setPriority] = useState('medium');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !subject.trim() || !message.trim()) {
      setError('Please fill in customer name, subject, and message.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const conv = await api.createConversation({
        customer_name: name,
        customer_email: email,
        customer_company: company,
        subject,
        category,
        priority,
        message,
        organization_id: activeOrgId || undefined,
      });
      onCreated(conv.id);
    } catch (err: any) {
      setError(err.message || 'Failed to create conversation');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[1300]" onClick={onClose}>
      <div
        className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] w-full max-w-lg mx-4 shadow-xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
          <h3 className="text-md font-semibold text-[var(--text-primary)]">New Conversation</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-[var(--bg-surface-hover)] text-[var(--text-tertiary)]">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Customer Info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Customer Name *</label>
              <input
                value={name} onChange={e => setName(e.target.value)}
                placeholder="Jane Doe"
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Company</label>
              <input
                value={company} onChange={e => setCompany(e.target.value)}
                placeholder="ACME Corp"
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Email</label>
            <input
              type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="jane@acme.com"
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Subject *</label>
            <input
              value={subject} onChange={e => setSubject(e.target.value)}
              placeholder="e.g. Can't connect Slack integration"
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none">
                <option>General</option>
                <option>Account Access</option>
                <option>Billing</option>
                <option>Technical</option>
                <option>Security</option>
                <option>Integrations</option>
                <option>Legal</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Priority</label>
              <select value={priority} onChange={e => setPriority(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] focus:outline-none">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>

          {/* Customer Message */}
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">Customer Message *</label>
            <textarea
              value={message} onChange={e => setMessage(e.target.value)}
              rows={4}
              placeholder="Type the customer's support message here... Try things like:&#10;• How do I reset my password?&#10;• I think someone hacked my account&#10;• How do I upgrade my billing plan?&#10;• What browsers are supported?"
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30 resize-y"
            />
          </div>

          {error && (
            <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">{error}</div>
          )}

          <div className="flex gap-2 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 px-3 py-2.5 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg bg-navy-600 hover:bg-navy-700 text-white text-sm font-medium transition-colors disabled:opacity-50">
              <Send className="w-3.5 h-3.5" />
              {submitting ? 'Creating...' : 'Create & Open'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
