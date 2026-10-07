import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SystemHealth } from '../types';
import { useStore } from '../stores/useStore';
import {
  Settings as SettingsIcon, Monitor, Palette, Shield, Database, Activity,
  Building2, Plus, Check, ChevronDown, ChevronRight, X, FolderTree,
} from 'lucide-react';

export default function SettingsPage() {
  const { theme, toggleTheme, user, organizations, setOrganizations, activeOrgId, setActiveOrg, addToast } = useStore();
  const [health, setHealth] = useState<SystemHealth | null>(null);

  // New Org Form State
  const [showOrgForm, setShowOrgForm] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgSlug, setNewOrgSlug] = useState('');
  const [newOrgDesc, setNewOrgDesc] = useState('');
  const [newOrgDeptName, setNewOrgDeptName] = useState('Support');
  const [isSubmittingOrg, setIsSubmittingOrg] = useState(false);

  // New Department Form State
  const [activeDeptOrgId, setActiveDeptOrgId] = useState<string | null>(null);
  const [deptName, setDeptName] = useState('');
  const [deptSlug, setDeptSlug] = useState('');
  const [isSubmittingDept, setIsSubmittingDept] = useState(false);

  useEffect(() => {
    api.getSystemHealth().catch(() => null).then(h => setHealth(h));
    refreshOrganizations();
  }, []);

  const refreshOrganizations = async () => {
    try {
      const orgs = await api.getOrganizations();
      setOrganizations(orgs);
    } catch {
      // ignore
    }
  };

  const handleNameChange = (val: string) => {
    setNewOrgName(val);
    const slug = val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    setNewOrgSlug(slug);
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName.trim() || !newOrgSlug.trim()) {
      addToast({ type: 'warning', message: 'Please provide organization name and slug.' });
      return;
    }

    setIsSubmittingOrg(true);
    try {
      const createdOrg = await api.createOrganization({
        name: newOrgName.trim(),
        slug: newOrgSlug.trim(),
        description: newOrgDesc.trim() || undefined,
      });

      // Optionally create initial department
      if (newOrgDeptName.trim()) {
        const dSlug = newOrgDeptName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        await api.createDepartment(createdOrg.id, {
          name: newOrgDeptName.trim(),
          slug: dSlug || 'support',
          description: 'General support department',
        }).catch(() => null);
      }

      await refreshOrganizations();
      setActiveOrg(createdOrg.id);
      addToast({ type: 'success', message: `Organization "${createdOrg.name}" created successfully!` });

      // Reset form
      setNewOrgName('');
      setNewOrgSlug('');
      setNewOrgDesc('');
      setNewOrgDeptName('Support');
      setShowOrgForm(false);
    } catch (err: any) {
      addToast({ type: 'error', message: err?.message || 'Failed to create organization.' });
    } finally {
      setIsSubmittingOrg(false);
    }
  };

  const handleCreateDepartment = async (orgId: string) => {
    if (!deptName.trim() || !deptSlug.trim()) {
      addToast({ type: 'warning', message: 'Please provide department name and slug.' });
      return;
    }

    setIsSubmittingDept(true);
    try {
      await api.createDepartment(orgId, {
        name: deptName.trim(),
        slug: deptSlug.trim(),
      });
      await refreshOrganizations();
      addToast({ type: 'success', message: `Department "${deptName}" added!` });
      setActiveDeptOrgId(null);
      setDeptName('');
      setDeptSlug('');
    } catch (err: any) {
      addToast({ type: 'error', message: err?.message || 'Failed to add department.' });
    } finally {
      setIsSubmittingDept(false);
    }
  };

  const StatusRow = ({ label, status }: { label: string; status: string }) => {
    const ok = ['connected', 'ready', 'loaded'].includes(status);
    return (
      <div className="flex items-center justify-between py-2">
        <span className="text-sm text-[var(--text-secondary)]">{label}</span>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${ok ? 'bg-green-500' : 'bg-amber-500'}`} />
          <span className={`text-sm ${ok ? 'text-green-600' : 'text-amber-600'}`}>{status.replace(/_/g, ' ')}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Settings & Administration</h2>
          <p className="text-xs text-[var(--text-tertiary)] mt-0.5">Manage organizations, departments, profiles, and copilot health</p>
        </div>
      </div>

      {/* Organizations & Workspaces */}
      <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-500" />
            <div>
              <h3 className="text-md font-semibold text-[var(--text-primary)]">Organizations & Workspaces</h3>
              <p className="text-xs text-[var(--text-tertiary)]">Multi-tenant segregation: each organization maintains isolated KB docs and tickets</p>
            </div>
          </div>
          <button
            onClick={() => setShowOrgForm(!showOrgForm)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-600 hover:bg-navy-700 text-white text-xs font-medium transition-colors"
          >
            {showOrgForm ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            {showOrgForm ? 'Cancel' : 'New Organization'}
          </button>
        </div>

        {/* Create Organization Form */}
        {showOrgForm && (
          <form onSubmit={handleCreateOrg} className="p-4 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] space-y-3 mt-3">
            <h4 className="text-sm font-semibold text-[var(--text-primary)]">Create New Organization</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Organization Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Acme Corporation"
                  value={newOrgName}
                  onChange={e => handleNameChange(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Slug Identifier *</label>
                <input
                  type="text"
                  placeholder="e.g. acme-corp"
                  value={newOrgSlug}
                  onChange={e => setNewOrgSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))}
                  className="w-full px-3 py-1.5 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Description (optional)</label>
              <input
                type="text"
                placeholder="e.g. Enterprise B2B SaaS platform and customer support team"
                value={newOrgDesc}
                onChange={e => setNewOrgDesc(e.target.value)}
                className="w-full px-3 py-1.5 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Initial Department</label>
                <input
                  type="text"
                  placeholder="e.g. Customer Support"
                  value={newOrgDeptName}
                  onChange={e => setNewOrgDeptName(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  disabled={isSubmittingOrg || !newOrgName.trim()}
                  className="w-full py-1.5 px-4 rounded bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs font-medium transition-colors"
                >
                  {isSubmittingOrg ? 'Creating Organization...' : 'Save & Set as Active Org'}
                </button>
              </div>
            </div>
          </form>
        )}

        {/* Organizations List */}
        <div className="divide-y divide-[var(--border)] border border-[var(--border)] rounded-lg overflow-hidden bg-[var(--bg-card)]">
          {organizations.map(org => {
            const isActive = org.id === activeOrgId;
            return (
              <div key={org.id} className="p-3.5 space-y-2 hover:bg-[var(--bg-surface-hover)] transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="font-semibold text-sm text-[var(--text-primary)]">{org.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-badge)] text-[var(--text-secondary)]">ID: {org.id}</span>
                    {isActive && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center gap-1">
                        <Check className="w-3 h-3" /> Active Workspace
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {!isActive && (
                      <button
                        onClick={() => {
                          setActiveOrg(org.id);
                          addToast({ type: 'info', message: `Switched to workspace "${org.name}"` });
                        }}
                        className="px-2.5 py-1 text-xs rounded border border-[var(--border)] hover:bg-[var(--bg-surface)] text-[var(--text-secondary)] transition-colors"
                      >
                        Switch To
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setActiveDeptOrgId(activeDeptOrgId === org.id ? null : org.id);
                        setDeptName('');
                        setDeptSlug('');
                      }}
                      className="px-2 py-1 text-[11px] rounded bg-[var(--bg-badge)] hover:bg-[var(--bg-surface)] text-[var(--text-secondary)] flex items-center gap-1 transition-colors"
                    >
                      <Plus className="w-3 h-3" /> Dept
                    </button>
                  </div>
                </div>

                {org.description && (
                  <p className="text-xs text-[var(--text-tertiary)]">{org.description}</p>
                )}

                {/* Departments pills */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1 mr-1">
                    <FolderTree className="w-3 h-3" /> Departments:
                  </span>
                  {org.departments && org.departments.length > 0 ? (
                    org.departments.map(dept => (
                      <span
                        key={dept.id}
                        className="text-[11px] px-2 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-secondary)]"
                      >
                        {dept.name}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px] italic text-[var(--text-tertiary)]">No departments yet</span>
                  )}
                </div>

                {/* Inline add department form */}
                {activeDeptOrgId === org.id && (
                  <div className="mt-2 p-2.5 rounded bg-[var(--bg-surface)] border border-[var(--border)] flex flex-wrap items-center gap-2">
                    <input
                      type="text"
                      placeholder="Dept Name (e.g. Sales)"
                      value={deptName}
                      onChange={e => {
                        setDeptName(e.target.value);
                        setDeptSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''));
                      }}
                      className="px-2 py-1 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)]"
                    />
                    <input
                      type="text"
                      placeholder="Slug (e.g. sales)"
                      value={deptSlug}
                      onChange={e => setDeptSlug(e.target.value)}
                      className="px-2 py-1 text-xs rounded border border-[var(--border)] bg-[var(--bg-input)] text-[var(--text-primary)] font-mono"
                    />
                    <button
                      onClick={() => handleCreateDepartment(org.id)}
                      disabled={isSubmittingDept || !deptName.trim()}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded text-xs font-medium"
                    >
                      {isSubmittingDept ? 'Adding...' : 'Add Department'}
                    </button>
                    <button
                      onClick={() => setActiveDeptOrgId(null)}
                      className="px-2 py-1 text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Profile */}
      <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
        <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Shield className="w-4 h-4 text-[var(--text-tertiary)]" /> Profile
        </h3>
        {user && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-[var(--text-tertiary)]">Name</span><span className="text-[var(--text-primary)]">{user.full_name}</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-tertiary)]">Email</span><span className="text-[var(--text-primary)]">{user.email}</span></div>
            <div className="flex justify-between"><span className="text-[var(--text-tertiary)]">Role</span><span className="text-[var(--text-primary)] capitalize">{user.role}</span></div>
          </div>
        )}
      </div>

      {/* Appearance */}
      <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
        <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Palette className="w-4 h-4 text-[var(--text-tertiary)]" /> Appearance
        </h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-[var(--text-primary)]">Theme</p>
            <p className="text-xs text-[var(--text-tertiary)]">Switch between light and dark mode</p>
          </div>
          <button
            onClick={toggleTheme}
            className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)] transition-colors capitalize"
          >
            {theme} mode
          </button>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
        <h3 className="text-md font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-[var(--text-tertiary)]" /> System Health
        </h3>
        {health ? (
          <div className="divide-y divide-[var(--border)]">
            <StatusRow label="Database" status={health.database} />
            <StatusRow label="RAG Index" status={health.rag_index} />
            <StatusRow label="Embedding Model" status={health.embedding_model} />
            <StatusRow label="LLM" status={health.llm} />
            <StatusRow label="Fine-tuned Adapter" status={health.model_adapter} />
          </div>
        ) : (
          <p className="text-sm text-[var(--text-tertiary)]">Unable to check system status</p>
        )}
      </div>

      {/* About */}
      <div className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-5">
        <h3 className="text-md font-semibold text-[var(--text-primary)] mb-2">About Bot-ए-rar</h3>
        <p className="text-sm text-[var(--text-secondary)]">
          AI-Powered Customer Support Copilot. Grounded answers, faster support, human control. Multi-tenant architecture with tenant-isolated knowledge bases.
        </p>
        <p className="text-xs text-[var(--text-tertiary)] mt-2">Version 2.0.0 • Multi-Tenant Enterprise Edition</p>
      </div>
    </div>
  );
}
