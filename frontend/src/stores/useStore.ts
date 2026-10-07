/** Global state store using Zustand (V2 — with org switcher) */
import { create } from 'zustand';
import type { User, Organization } from '../types';

interface AppState {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;

  // Organization switcher
  organizations: Organization[];
  activeOrgId: string | null;
  setOrganizations: (orgs: Organization[]) => void;
  setActiveOrg: (orgId: string) => void;

  // Theme
  theme: 'light' | 'dark';
  toggleTheme: () => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Command palette
  commandPaletteOpen: boolean;
  setCommandPalette: (open: boolean) => void;

  // Toast
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
}

export const useStore = create<AppState>((set, get) => ({
  // Auth
  user: null,
  token: localStorage.getItem('resolveai_token'),
  setAuth: (user, token) => {
    localStorage.setItem('resolveai_token', token);
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem('resolveai_token');
    localStorage.removeItem('resolveai_active_org');
    set({ user: null, token: null, activeOrgId: null });
  },

  // Organization switcher
  organizations: [],
  activeOrgId: localStorage.getItem('resolveai_active_org'),
  setOrganizations: (orgs) => {
    set({ organizations: orgs });
    // Auto-select first org if none selected
    const current = get().activeOrgId;
    if (!current && orgs.length > 0) {
      localStorage.setItem('resolveai_active_org', orgs[0].id);
      set({ activeOrgId: orgs[0].id });
    }
  },
  setActiveOrg: (orgId) => {
    localStorage.setItem('resolveai_active_org', orgId);
    set({ activeOrgId: orgId });
  },

  // Theme
  theme: (localStorage.getItem('resolveai_theme') as 'light' | 'dark') || 'light',
  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('resolveai_theme', next);
    document.documentElement.setAttribute('data-theme', next);
    set({ theme: next });
  },

  // Sidebar
  sidebarCollapsed: false,
  toggleSidebar: () => set(s => ({ sidebarCollapsed: !s.sidebarCollapsed })),

  // Command palette
  commandPaletteOpen: false,
  setCommandPalette: (open) => set({ commandPaletteOpen: open }),

  // Toasts
  toasts: [],
  addToast: (toast) => {
    const id = Math.random().toString(36).slice(2);
    set(s => ({ toasts: [...s.toasts, { ...toast, id }] }));
    setTimeout(() => get().removeToast(id), 4000);
  },
  removeToast: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}));
