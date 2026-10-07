/** API service layer — all backend communication (V2) */
import type {
  TokenResponse, ConversationListItem, ConversationDetail,
  DraftResponse, KnowledgeDoc, KnowledgeGap, EvaluationMetric,
  Analytics, ModelInsights, SystemHealth, AuditLog, Organization,
  Department, KnowledgeHealth,
} from '../types';

const BASE = '/api';

function getToken(): string | null {
  return localStorage.getItem('resolveai_token');
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };
  // Only set Content-Type for non-FormData requests
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${url}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────
export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<TokenResponse['user']>('/auth/me'),

  // ── Organizations ──────────────────────────────────────
  getOrganizations: () => request<Organization[]>('/organizations'),

  getOrganization: (id: string) => request<Organization>(`/organizations/${id}`),

  createOrganization: (data: { name: string; slug: string; description?: string }) =>
    request<Organization>('/organizations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  createDepartment: (orgId: string, data: { name: string; slug: string; description?: string }) =>
    request<Department>(`/organizations/${orgId}/departments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // ── Conversations ───────────────────────────────────────
  getConversations: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<ConversationListItem[]>(`/conversations${qs}`);
  },

  createConversation: (data: {
    customer_name: string;
    customer_email?: string;
    customer_company?: string;
    subject: string;
    category?: string;
    priority?: string;
    message: string;
    organization_id?: string;
  }) =>
    request<ConversationDetail>('/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getConversation: (id: string) =>
    request<ConversationDetail>(`/conversations/${id}`),

  // ── Drafts ──────────────────────────────────────────────
  generateDraft: (conversationId: string, opts?: { tone?: string; length?: string; focus?: string }) =>
    request<DraftResponse>(`/drafts/conversations/${conversationId}/draft`, {
      method: 'POST',
      body: JSON.stringify(opts || {}),
    }),

  approveDraft: (draftId: string, editedReply?: string) =>
    request<any>(`/drafts/${draftId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ edited_reply: editedReply }),
    }),

  rejectDraft: (draftId: string) =>
    request<any>(`/drafts/${draftId}/reject`, { method: 'POST' }),

  regenerateDraft: (draftId: string, opts?: { tone?: string; length?: string; focus?: string }) =>
    request<DraftResponse>(`/drafts/${draftId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify(opts || {}),
    }),

  escalateDraft: (draftId: string) =>
    request<any>(`/drafts/${draftId}/escalate`, { method: 'POST' }),

  // ── Knowledge ───────────────────────────────────────────
  getKnowledge: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<KnowledgeDoc[]>(`/knowledge${qs}`);
  },

  getKnowledgeDoc: (id: string) =>
    request<KnowledgeDoc>(`/knowledge/${id}`),

  getCategories: () => request<string[]>('/knowledge/categories'),

  getKnowledgeGaps: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return request<KnowledgeGap[]>(`/knowledge/gaps${qs}`);
  },

  getKnowledgeHealth: (orgId?: string) => {
    const qs = orgId ? `?organization_id=${orgId}` : '';
    return request<KnowledgeHealth>(`/knowledge/health${qs}`);
  },

  searchKnowledge: (query: string, topK = 5) =>
    request<any[]>('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }),

  uploadKnowledge: (formData: FormData) =>
    request<{ status: string; doc_id: string; title: string; message: string }>('/knowledge/upload', {
      method: 'POST',
      body: formData,
    }),

  reindexKnowledge: () =>
    request<{ status: string; message: string; output?: string }>('/knowledge/reindex', {
      method: 'POST',
    }),

  loadTrndingPack: () =>
    request<{
      status: string;
      organization_id: string;
      message: string;
      knowledge_docs_count: number;
      products_count: number;
      faqs_count: number;
      conversations_count: number;
    }>('/knowledge/load-trnding-pack', {
      method: 'POST',
    }),

  archiveKnowledgeDoc: (docId: string) =>
    request<any>(`/knowledge/${docId}/archive`, { method: 'POST' }),

  // ── Analytics ───────────────────────────────────────────
  getAnalytics: () => request<Analytics>('/analytics'),

  // ── Evaluation ──────────────────────────────────────────
  getEvaluations: (type?: string) => {
    const qs = type ? `?eval_type=${type}` : '';
    return request<EvaluationMetric[]>(`/evaluation${qs}`);
  },

  // ── Model ───────────────────────────────────────────────
  getModelInsights: () => request<ModelInsights>('/model'),

  // ── System ──────────────────────────────────────────────
  getSystemHealth: () => request<SystemHealth>('/system/health'),

  // ── Audit ───────────────────────────────────────────────
  getAuditLogs: (conversationId?: string) => {
    const qs = conversationId ? `?conversation_id=${conversationId}` : '';
    return request<AuditLog[]>(`/audit${qs}`);
  },
};
