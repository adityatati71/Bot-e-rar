// ── API Types ─────────────────────────────────────────────── V2

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
  departments: Department[];
  created_at: string;
}

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string;
  is_active: boolean;
  organization_id?: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ConversationListItem {
  id: string;
  organization_id?: string;
  customer_name: string;
  customer_email?: string;
  customer_company?: string;
  subject: string;
  category?: string;
  priority: string;
  status: string;
  agent_id?: string;
  created_at: string;
  updated_at: string;
  latest_message?: string;
  draft_confidence?: number;
  draft_status?: string;
  source_count?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender: string;
  content: string;
  created_at: string;
}

export interface CitationItem {
  faq_id: string;
  title: string;
  snippet: string;
  relevance_score: number;
  version?: string;
  updated_at?: string;
  category?: string;
  authority?: string;
}

export interface ConfidenceDetail {
  score: number;
  level: string;
  reasons: string[];
  retrieval_relevance?: number;
  source_coverage?: number;
  freshness?: number;
  consistency?: number;
  authority?: number;
  answerability?: number;
}

export interface KnowledgeGapInfo {
  needed: boolean;
  reason?: string;
  missing_topic?: string;
}

export interface EscalationInfo {
  required: boolean;
  reason?: string;
  recommended_team?: string;
}

export interface SourceConflictInfo {
  detected: boolean;
  reason?: string;
  conflicting_sources?: string[];
  preferred_source?: string;
}

export interface EvidenceCoverageInfo {
  score: number;
  covered: string[];
  missing: string[];
}

export interface ToneCheck {
  professional: boolean;
  concise: boolean;
  empathetic: boolean;
}

export interface DraftResponse {
  id: string;
  conversation_id: string;
  draft_reply: string;
  short_summary?: string;
  status: string;
  confidence: ConfidenceDetail;
  citations: CitationItem[];
  knowledge_gap: KnowledgeGapInfo;
  escalation: EscalationInfo;
  source_conflict?: SourceConflictInfo;
  evidence_coverage?: EvidenceCoverageInfo;
  tone_check: ToneCheck;
  model_version?: string;
  retrieval_latency_ms?: number;
  generation_latency_ms?: number;
  total_latency_ms?: number;
  edited_reply?: string;
  edit_distance?: number;
  approved_at?: string;
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  organization_id?: string;
  organization_name?: string;
  customer_name: string;
  customer_email?: string;
  customer_company?: string;
  subject: string;
  category?: string;
  priority: string;
  status: string;
  agent_id?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
  drafts: DraftResponse[];
}

export interface KnowledgeDoc {
  id: string;
  doc_id: string;
  organization_id?: string;
  organization_name?: string;
  department_id?: string;
  title: string;
  category: string;
  document_type?: string;
  authority?: string;
  content: string;
  keywords: string[];
  version: string;
  status: string;
  owner?: string;
  source_url?: string;
  source_filename?: string;
  usage_count: number;
  avg_relevance: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeGap {
  id: string;
  topic: string;
  description: string;
  question_pattern?: string;
  frequency: number;
  impact: string;
  status: string;
  recommended_action?: string;
  conversation_id?: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationMetric {
  id: string;
  eval_type: string;
  metric_name: string;
  metric_value: number;
  details: Record<string, any>;
  dataset_version?: string;
  model_version?: string;
  created_at: string;
}

export interface Analytics {
  total_conversations: number;
  total_drafts: number;
  approval_rate: number;
  rejection_rate: number;
  avg_confidence: number;
  escalation_rate: number;
  knowledge_gap_count: number;
  avg_edit_distance: number;
  conversations_by_status: Record<string, number>;
  conversations_by_priority: Record<string, number>;
  conversations_by_category: Record<string, number>;
  confidence_distribution: Record<string, number>;
  drafts_over_time: any[];
  approval_over_time: any[];
}

export interface ModelInsights {
  current_model: string;
  base_model: string;
  fine_tuning_method?: string;
  adapter_path?: string;
  training_dataset_size?: number;
  validation_loss?: number;
  eval_metrics: Record<string, number>;
  quantization?: string;
  context_size?: number;
  is_active: boolean;
  version?: string;
}

export interface SystemHealth {
  database: string;
  rag_index: string;
  embedding_model: string;
  llm: string;
  model_adapter: string;
}

export interface AuditLog {
  id: string;
  conversation_id?: string;
  user_id?: string;
  action: string;
  previous_state?: string;
  new_state?: string;
  details: Record<string, any>;
  ai_version?: string;
  sources_used: string[];
  created_at: string;
}

export interface KnowledgeHealth {
  total_documents: number;
  active_documents: number;
  categories: number;
  fresh_documents: number;
  stale_documents: number;
  open_gaps: number;
  freshness_score: number;
  coverage_score: number;
  health_score: number;
}
