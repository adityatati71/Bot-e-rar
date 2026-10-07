import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useStore } from '../stores/useStore';
import {
  Inbox, BookOpen, AlertTriangle, BarChart3, Activity, Brain,
  Settings, Sun, Moon, Search, ChevronLeft, ChevronRight,
  LayoutDashboard, LogOut, Shield, Building2, Upload,
} from 'lucide-react';
import { useEffect } from 'react';
import { api } from '../services/api';

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inbox', icon: Inbox, label: 'Inbox' },
  { to: '/knowledge', icon: BookOpen, label: 'Knowledge' },
  { to: '/upload', icon: Upload, label: 'Add Knowledge' },
  { to: '/gaps', icon: AlertTriangle, label: 'Gaps' },
  { to: '/evaluation', icon: Activity, label: 'Evaluation' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/model', icon: Brain, label: 'Model Insights' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  const {
    user, theme, toggleTheme, sidebarCollapsed, toggleSidebar,
    logout, setCommandPalette, organizations, activeOrgId, setOrganizations, setActiveOrg,
  } = useStore();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      api.getMe().then(u => {
        const token = localStorage.getItem('resolveai_token');
        if (token) useStore.getState().setAuth(u, token);
      }).catch(() => {});
    }
    // Load organizations
    api.getOrganizations().then(orgs => setOrganizations(orgs)).catch(() => {});
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPalette(true);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const pageTitle = NAV.find(n => location.pathname.startsWith(n.to))?.label
    || (location.pathname.includes('conversation') ? 'Conversation' : 'Bot-ए-rar');

  const activeOrg = organizations.find(o => o.id === activeOrgId);

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-app)]">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-[var(--bg-sidebar)] text-[var(--sidebar-text)] transition-all duration-200 ${
          sidebarCollapsed ? 'w-14' : 'w-60'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 px-4 h-12 border-b border-white/5">
          <Shield className="w-5 h-5 text-navy-400 shrink-0" />
          {!sidebarCollapsed && (
            <span className="text-md font-semibold text-white tracking-tight">Bot-ए-rar</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-2 px-2 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-2.5 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? 'bg-[var(--sidebar-active)] text-white'
                    : 'hover:bg-[var(--sidebar-hover)] text-[var(--sidebar-text)]'
                } ${sidebarCollapsed ? 'justify-center' : ''}`
              }
              title={label}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom */}
        <div className="border-t border-white/5 p-2 space-y-1">
          {!sidebarCollapsed && user && (
            <div className="px-2.5 py-2 text-xs">
              <div className="text-white/80 truncate">{user.full_name}</div>
              <div className="text-white/40 truncate">{user.email}</div>
            </div>
          )}
          <button
            onClick={logout}
            className="flex items-center gap-3 px-2.5 py-2 rounded-md text-sm hover:bg-[var(--sidebar-hover)] w-full transition-colors"
            title="Log out"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            {!sidebarCollapsed && <span>Log out</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <header className="flex items-center gap-4 h-12 px-4 bg-[var(--bg-topbar)] border-b border-[var(--border)] shrink-0">
          <button
            onClick={toggleSidebar}
            className="p-1 rounded hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)] transition-colors"
          >
            {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>

          <h1 className="text-md font-semibold text-[var(--text-primary)]">{pageTitle}</h1>

          <div className="flex-1" />

          {/* Organization Switcher */}
          {organizations.length > 0 && (
            <div className="flex items-center gap-2">
              <Building2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <select
                value={activeOrgId || ''}
                onChange={e => {
                  if (e.target.value === '__manage__') {
                    navigate('/settings');
                  } else {
                    setActiveOrg(e.target.value);
                  }
                }}
                className="px-2 py-1 rounded-md border border-[var(--border)] bg-[var(--bg-input)] text-xs text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-navy-500/30 font-medium"
              >
                {organizations.map(org => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
                <option value="__manage__">+ Manage / New Org...</option>
              </select>
            </div>
          )}

          {/* Search trigger */}
          <button
            onClick={() => setCommandPalette(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[var(--border)] text-xs text-[var(--text-tertiary)] hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search</span>
            <kbd className="hidden sm:inline px-1.5 py-0.5 rounded bg-[var(--bg-badge)] text-[10px] font-mono">⌘K</kbd>
          </button>

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded hover:bg-[var(--bg-surface-hover)] text-[var(--text-secondary)] transition-colors"
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
