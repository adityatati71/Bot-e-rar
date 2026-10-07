import { useState, useRef } from 'react';
import {
  Upload, FileText, AlertCircle, CheckCircle, RefreshCw,
  Building2, Sparkles, FolderUp, Layers, CheckSquare, ArrowRight,
  Database, HelpCircle, ShoppingBag, MessageSquare
} from 'lucide-react';
import { api } from '../services/api';
import { useStore } from '../stores/useStore';

interface UploadStatusItem {
  name: string;
  type: string;
  status: 'pending' | 'success' | 'error';
  message: string;
  count?: number;
}

export default function UploadPage() {
  const { organizations, activeOrgId, setActiveOrg, setOrganizations, addToast } = useStore();
  const fileRef = useRef<HTMLInputElement>(null);

  const [files, setFiles] = useState<File[]>([]);
  const [category, setCategory] = useState('General');
  const [authority, setAuthority] = useState('approved_faq');
  const [docType, setDocType] = useState('faq');
  const [uploading, setUploading] = useState(false);
  const [reindexing, setReindexing] = useState(false);
  const [loadingTrnding, setLoadingTrnding] = useState(false);
  const [uploadResults, setUploadResults] = useState<UploadStatusItem[]>([]);

  const detectFileType = (file: File) => {
    const name = file.name.toLowerCase();
    if (name.includes('organization')) return { label: 'Organization Data', icon: Building2, color: 'text-indigo-400' };
    if (name.includes('department')) return { label: 'Departments', icon: Layers, color: 'text-blue-400' };
    if (name.includes('knowledge')) return { label: 'Knowledge Docs', icon: FileText, color: 'text-emerald-400' };
    if (name.includes('product')) return { label: 'Products Catalog', icon: ShoppingBag, color: 'text-amber-400' };
    if (name.includes('faq')) return { label: 'FAQs Collection', icon: HelpCircle, color: 'text-purple-400' };
    if (name.includes('conversation')) return { label: 'Support Conversations', icon: MessageSquare, color: 'text-sky-400' };
    if (name.endsWith('.pdf')) return { label: 'PDF Document', icon: FileText, color: 'text-rose-400' };
    return { label: 'Document', icon: FileText, color: 'text-gray-400' };
  };

  const handleFilesSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
      setUploadResults([]);
    }
  };

  const handleBatchUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    const results: UploadStatusItem[] = [];

    for (const f of files) {
      try {
        const formData = new FormData();
        formData.append('file', f);
        formData.append('organization_id', activeOrgId || '');
        formData.append('category', category);
        formData.append('authority', authority);
        formData.append('document_type', docType);

        const res: any = await api.uploadKnowledge(formData);
        results.push({
          name: f.name,
          type: res.type || 'document',
          status: 'success',
          message: res.message || `Uploaded as ${res.title}`,
          count: res.count || 1,
        });
      } catch (err: any) {
        results.push({
          name: f.name,
          type: 'error',
          status: 'error',
          message: err.message || 'Upload failed',
        });
      }
    }

    setUploadResults(results);
    setFiles([]);
    if (fileRef.current) fileRef.current.value = '';
    setUploading(false);

    // Refresh organizations list in case organization.json was uploaded
    try {
      const orgs = await api.getOrganizations();
      setOrganizations(orgs);
    } catch {}

    const successCount = results.filter(r => r.status === 'success').length;
    if (successCount > 0) {
      addToast({
        message: `Successfully processed ${successCount} file(s)!`,
        type: 'success',
      });
    }
  };

  const handleLoadTrndingPack = async () => {
    setLoadingTrnding(true);
    try {
      const res = await api.loadTrndingPack();
      addToast({
        message: `TRNDING Test Pack loaded! (${res.knowledge_docs_count} docs, ${res.products_count} products, ${res.faqs_count} FAQs, ${res.conversations_count} conversations)`,
        type: 'success',
      });
      // Refresh organizations and select TRNDING
      const orgs = await api.getOrganizations();
      setOrganizations(orgs);
      const trndingOrg = orgs.find(o => o.slug === 'trnding' || o.id === 'org-trnding');
      if (trndingOrg) {
        setActiveOrg(trndingOrg.id);
      }
    } catch (err: any) {
      addToast({ message: err.message || 'Failed to load test pack', type: 'error' });
    } finally {
      setLoadingTrnding(false);
    }
  };

  const handleReindex = async () => {
    setReindexing(true);
    try {
      const result = await api.reindexKnowledge();
      if (result.status === 'success') {
        addToast({ message: 'Indices rebuilt and reloaded successfully!', type: 'success' });
      } else {
        addToast({ message: result.message, type: 'error' });
      }
    } catch (err: any) {
      addToast({ message: err.message, type: 'error' });
    } finally {
      setReindexing(false);
    }
  };

  const activeOrg = organizations.find(o => o.id === activeOrgId);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-[var(--text-primary)]">Add Knowledge & Tenant Data</h2>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Upload JSON datasets, PDFs, Markdown or plain text. The system automatically detects organization profiles, departments, FAQs, product catalogs, and support conversations.
        </p>
      </div>

      {/* 1-Click TRNDING MVP Test Pack Banner */}
      <div className="p-5 rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-blue-950/30 backdrop-blur-sm relative overflow-hidden">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-400" /> Hackathon Demo Ready
              </span>
              <h3 className="text-base font-semibold text-white">TRNDING Benchmark Test Pack</h3>
            </div>
            <p className="text-xs text-indigo-200/80 max-w-xl">
              1-Click instant setup of the complete TRNDING tenant dataset: <strong>16 Knowledge Docs</strong>, <strong>10 Products</strong>, <strong>20 FAQs</strong>, <strong>9 Inbox Conversations</strong>, and departments. Automatically builds FAISS vector embeddings and BM25 indices.
            </p>
            <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-indigo-300/70">
              <span className="flex items-center gap-1">✓ Organization Profile</span>
              <span className="flex items-center gap-1">✓ Auto Vector Embeddings</span>
              <span className="flex items-center gap-1">✓ Multi-tenant Isolation</span>
              <span className="flex items-center gap-1">✓ Grounded RAG Citations</span>
            </div>
          </div>
          <button
            onClick={handleLoadTrndingPack}
            disabled={loadingTrnding}
            className="px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2 shrink-0 disabled:opacity-50"
          >
            {loadingTrnding ? (
              <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Loading & Indexing...</>
            ) : (
              <><Sparkles className="w-3.5 h-3.5" /> ⚡ 1-Click Load TRNDING Pack</>
            )}
          </button>
        </div>
      </div>

      {/* Target Tenant Selector */}
      <div className="flex items-center justify-between p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)]">
        <div className="flex items-center gap-2.5">
          <Building2 className="w-4 h-4 text-navy-400" />
          <span className="text-xs font-medium text-[var(--text-secondary)]">Active Tenant for Upload:</span>
          <select
            value={activeOrgId || ''}
            onChange={e => setActiveOrg(e.target.value)}
            className="px-2.5 py-1 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] font-medium"
          >
            {organizations.map(o => (
              <option key={o.id} value={o.id}>{o.name} ({o.id})</option>
            ))}
          </select>
        </div>
        <span className="text-[11px] text-[var(--text-tertiary)]">
          {activeOrg?.description || 'Active organization for documents'}
        </span>
      </div>

      {/* Upload Zone */}
      <div className="card p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">
            Select or Drop Files (Multi-file JSON / PDF / TXT / MD)
          </label>
          <div
            onClick={() => fileRef.current?.click()}
            className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-[var(--border)] rounded-xl cursor-pointer hover:border-navy-500/50 hover:bg-navy-500/5 transition-all"
          >
            <FolderUp className="w-9 h-9 text-navy-400 mb-2.5" />
            <p className="text-sm font-medium text-[var(--text-primary)]">
              {files.length > 0 ? `${files.length} file(s) selected` : 'Click or drop files here to upload'}
            </p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">
              Supports: organization.json, departments.json, knowledge_documents.json, products.json, faqs.json, support_conversations.json, PDF, TXT, MD
            </p>
          </div>
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".json,.pdf,.txt,.md,.markdown"
            className="hidden"
            onChange={handleFilesSelected}
          />
        </div>

        {/* Selected files preview */}
        {files.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              Selected Files ({files.length}):
            </p>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto p-1">
              {files.map((f, i) => {
                const info = detectFileType(f);
                const Icon = info.icon;
                return (
                  <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-[var(--bg-app)] border border-[var(--border)] text-xs">
                    <Icon className={`w-4 h-4 shrink-0 ${info.color}`} />
                    <span className="truncate font-medium text-[var(--text-primary)]">{f.name}</span>
                    <span className="ml-auto text-[10px] text-[var(--text-tertiary)] shrink-0">
                      {info.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Optional Metadata Defaults for Generic Single Documents */}
        <div className="grid grid-cols-3 gap-4 pt-1 border-t border-[var(--border)]">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Category (Default)</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded border border-[var(--border)] bg-[var(--bg-input)] text-xs text-[var(--text-primary)]"
            >
              {['General', 'Account Access', 'Billing', 'API', 'Security', 'Integrations', 'Troubleshooting', 'Products', 'FAQ', 'Company'].map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Authority Level</label>
            <select
              value={authority}
              onChange={e => setAuthority(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded border border-[var(--border)] bg-[var(--bg-input)] text-xs text-[var(--text-primary)]"
            >
              <option value="official_policy">Official Policy</option>
              <option value="official_docs">Official Docs</option>
              <option value="approved_faq">Approved FAQ</option>
              <option value="internal_article">Internal Article</option>
              <option value="agent_notes">Agent Notes</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Document Type</label>
            <select
              value={docType}
              onChange={e => setDocType(e.target.value)}
              className="w-full px-2.5 py-1.5 rounded border border-[var(--border)] bg-[var(--bg-input)] text-xs text-[var(--text-primary)]"
            >
              <option value="faq">FAQ</option>
              <option value="policy">Policy</option>
              <option value="documentation">Documentation</option>
              <option value="troubleshooting">Troubleshooting</option>
              <option value="guide">Guide</option>
            </select>
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={handleBatchUpload}
          disabled={files.length === 0 || uploading}
          className="btn-primary w-full py-2.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {uploading ? (
            <><RefreshCw className="w-4 h-4 animate-spin" /> Processing & Ingesting Files...</>
          ) : (
            <><Upload className="w-4 h-4" /> Upload {files.length > 0 ? `${files.length} Selected File(s)` : 'Files'}</>
          )}
        </button>
      </div>

      {/* Upload Results Summary */}
      {uploadResults.length > 0 && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Ingestion Summary</h3>
            <span className="text-xs text-[var(--text-tertiary)]">{uploadResults.length} files processed</span>
          </div>
          <div className="space-y-2">
            {uploadResults.map((res, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
                  res.status === 'success'
                    ? 'bg-green-500/5 border-green-500/20 text-green-400'
                    : 'bg-red-500/5 border-red-500/20 text-red-400'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {res.status === 'success' ? (
                    <CheckCircle className="w-4 h-4 shrink-0 text-green-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  )}
                  <div>
                    <span className="font-semibold text-[var(--text-primary)]">{res.name}</span>
                    <p className="text-[11px] text-[var(--text-secondary)] mt-0.5">{res.message}</p>
                  </div>
                </div>
                {res.count && (
                  <span className="px-2 py-0.5 rounded text-[10px] bg-navy-500/20 text-navy-300 font-medium shrink-0">
                    +{res.count} items
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Re-index section */}
      <div className="card p-5">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">FAISS + BM25 Search Indices</h3>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Re-building indices encodes all active knowledge chunks using sentence-transformers (all-MiniLM-L6-v2) and synchronizes BM25 sparse keyword indices across all tenants.
            </p>
            <button
              onClick={handleReindex}
              disabled={reindexing}
              className="btn-secondary mt-3 flex items-center gap-2 text-xs"
            >
              {reindexing ? (
                <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Rebuilding indices...</>
              ) : (
                <><RefreshCw className="w-3.5 h-3.5" /> Re-index Knowledge Base</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
