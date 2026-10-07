import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../stores/useStore';
import {
  Search, Inbox, BookOpen, BarChart3, Activity, Brain,
  Settings, Moon, Sun, Sparkles,
} from 'lucide-react';

const COMMANDS = [
  { id: 'inbox', label: 'Open Inbox', icon: Inbox, action: '/inbox' },
  { id: 'knowledge', label: 'Open Knowledge Base', icon: BookOpen, action: '/knowledge' },
  { id: 'analytics', label: 'View Analytics', icon: BarChart3, action: '/analytics' },
  { id: 'evaluation', label: 'View Evaluations', icon: Activity, action: '/evaluation' },
  { id: 'model', label: 'Model Insights', icon: Brain, action: '/model' },
  { id: 'settings', label: 'Open Settings', icon: Settings, action: '/settings' },
  { id: 'theme', label: 'Toggle Dark Mode', icon: Moon, action: 'theme' },
  { id: 'dashboard', label: 'Dashboard', icon: Sparkles, action: '/dashboard' },
];

export default function CommandPalette() {
  const { commandPaletteOpen, setCommandPalette, toggleTheme } = useStore();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery('');
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  const filtered = COMMANDS.filter(c =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  const execute = (cmd: typeof COMMANDS[0]) => {
    setCommandPalette(false);
    if (cmd.action === 'theme') {
      toggleTheme();
    } else {
      navigate(cmd.action);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && filtered[selected]) { execute(filtered[selected]); }
    if (e.key === 'Escape') { setCommandPalette(false); }
  };

  if (!commandPaletteOpen) return null;

  return (
    <div className="fixed inset-0 z-[var(--z-command)] flex items-start justify-center pt-[20vh]"
      onClick={() => setCommandPalette(false)}>
      <div className="absolute inset-0 bg-black/50" />
      <div className="relative w-full max-w-md mx-4 bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] shadow-xl overflow-hidden"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)]">
          <Search className="w-4 h-4 text-[var(--text-tertiary)]" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => { setQuery(e.target.value); setSelected(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Type a command..."
            className="flex-1 bg-transparent text-md text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none"
          />
          <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-badge)] text-[10px] font-mono text-[var(--text-tertiary)]">ESC</kbd>
        </div>
        <div className="max-h-64 overflow-y-auto py-1">
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              onClick={() => execute(cmd)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                i === selected ? 'bg-[var(--bg-surface-active)] text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)]'
              }`}
            >
              <cmd.icon className="w-4 h-4 shrink-0" />
              {cmd.label}
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="px-4 py-6 text-sm text-[var(--text-tertiary)] text-center">No commands found</p>
          )}
        </div>
      </div>
    </div>
  );
}
