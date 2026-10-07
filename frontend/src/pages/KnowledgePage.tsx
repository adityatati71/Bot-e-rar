import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { KnowledgeDoc } from '../types';
import { Search, BookOpen, Clock, Tag, ExternalLink, Building2 } from 'lucide-react';
import { useStore } from '../stores/useStore';

export default function KnowledgePage() {
  const { activeOrgId, organizations } = useStore();
  const [docs, setDocs] = useState<KnowledgeDoc[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDoc | null>(null);
  const [filterActiveOrg, setFilterActiveOrg] = useState(false);

  const activeOrg = organizations.find(o => o.id === activeOrgId);

  useEffect(() => {
    setLoading(true);
    const params = filterActiveOrg && activeOrgId ? { organization_id: activeOrgId } : undefined;
    Promise.all([
      api.getKnowledge(params),
      api.getCategories().catch(() => []),
    ]).then(([d, c]) => {
      setDocs(d); setCategories(c); setLoading(false);
    });
  }, [activeOrgId, filterActiveOrg]);

  const filtered = docs.filter(d => {
    if (search && !d.title.toLowerCase().includes(search.toLowerCase()) &&
        !d.content.toLowerCase().includes(search.toLowerCase())) return false;
    if (category !== 'all' && d.category !== category) return false;
    return true;
  });

  const daysAgo = (d: string) => {
    const days = Math.floor((Date.now() - new Date(d).getTime()) / 86400000);
    return days <= 0 ? 'Today' : days === 1 ? '1 day ago' : `${days} days ago`;
  };

  return (
    <div className="flex h-full">
      {/* List */}
      <div className={`${selectedDoc ? 'w-2/5' : 'w-full max-w-4xl mx-auto'} flex flex-col border-r border-[var(--border)] transition-all`}>
        <div className="p-4 space-y-3 border-b border-[var(--border)]">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">Knowledge Base</h2>
            {activeOrg && (
              <button
                onClick={() => setFilterActiveOrg(!filterActiveOrg)}
                className={`text-xs px-2.5 py-1 rounded-md border transition-colors flex items-center gap-1.5 ${
                  filterActiveOrg
                    ? 'bg-navy-600 text-white border-navy-500'
                    : 'bg-[var(--bg-input)] text-[var(--text-secondary)] border-[var(--border)] hover:bg-[var(--bg-surface-hover)]'
                }`}
              >
                <Building2 className="w-3.5 h-3.5" />
                {filterActiveOrg ? `${activeOrg.name} only` : 'All Organizations'}
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search articles..." className="w-full pl-9 pr-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm focus:outline-none focus:ring-2 focus:ring-navy-500/30" />
            </div>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-sm focus:outline-none">
              <option value="all">All Categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <p className="text-xs text-[var(--text-tertiary)]">{filtered.length} articles</p>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? [...Array(6)].map((_, i) => <div key={i} className="h-20 skeleton rounded-lg" />) :
            filtered.map(doc => (
              <button key={doc.id} onClick={() => setSelectedDoc(doc)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${
                  selectedDoc?.id === doc.id ? 'border-navy-500 bg-navy-50 dark:bg-navy-950' : 'border-[var(--border)] hover:border-[var(--border-strong)] bg-[var(--bg-surface)]'
                }`}>
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">{doc.title}</p>
                    <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-tertiary)]">
                      <span className="flex items-center gap-1"><Tag className="w-3 h-3" />{doc.category}</span>
                      {doc.organization_name && (
                        <span className="flex items-center gap-1 text-navy-400 font-medium">
                          <Building2 className="w-3 h-3" />{doc.organization_name}
                        </span>
                      )}
                      <span>v{doc.version}</span>
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{daysAgo(doc.updated_at)}</span>
                    </div>
                  </div>
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                    doc.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600'
                  }`}>{doc.status}</span>
                </div>
              </button>
            ))
          }
        </div>
      </div>

      {/* Detail */}
      {selectedDoc && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-[var(--border)]">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">{selectedDoc.title}</h3>
                <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-tertiary)]">
                  <span>{selectedDoc.doc_id}</span>
                  <span>{selectedDoc.category}</span>
                  <span>v{selectedDoc.version}</span>
                  {selectedDoc.owner && <span>Owner: {selectedDoc.owner}</span>}
                </div>
              </div>
              <button onClick={() => setSelectedDoc(null)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-sm">✕</button>
            </div>
            <div className="flex gap-4 mt-3 text-xs">
              <div className="px-2 py-1 rounded bg-[var(--bg-badge)]">Used by {selectedDoc.usage_count} AI responses</div>
              {selectedDoc.avg_relevance > 0 && <div className="px-2 py-1 rounded bg-[var(--bg-badge)]">Avg relevance {Math.round(selectedDoc.avg_relevance * 100)}%</div>}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="prose prose-sm max-w-none text-[var(--text-primary)]">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{selectedDoc.content}</pre>
            </div>
            {selectedDoc.keywords.length > 0 && (
              <div className="mt-4 pt-4 border-t border-[var(--border)]">
                <span className="text-xs text-[var(--text-tertiary)]">Keywords: </span>
                {selectedDoc.keywords.map(k => (
                  <span key={k} className="inline-block px-2 py-0.5 rounded bg-[var(--bg-badge)] text-xs text-[var(--text-secondary)] mr-1 mb-1">{k}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
