import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../stores/useStore';
import { api } from '../services/api';
import { Shield, ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('sarah@resolveai.demo');
  const [password, setPassword] = useState('demo123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { setAuth, theme, toggleTheme } = useStore();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.login(email, password);
      setAuth(res.user, res.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-app)] px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-navy-950 mb-4">
            <Shield className="w-6 h-6 text-navy-400" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Bot-ए-rar</h1>
          <p className="text-md text-[var(--text-secondary)] mt-1">AI Support Copilot</p>
          <p className="text-sm text-[var(--text-tertiary)] mt-2">
            Grounded answers. Faster support. Human control.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="bg-[var(--bg-surface)] rounded-xl border border-[var(--border)] p-6 shadow-sm">
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-md text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30 focus:border-navy-500 transition-colors"
                placeholder="you@company.com"
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[var(--text-secondary)] mb-1.5">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border-input)] bg-[var(--bg-input)] text-md text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-navy-500/30 focus:border-navy-500 transition-colors"
                placeholder="••••••••"
                required
              />
            </div>

            {error && (
              <div className="px-3 py-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-navy-600 hover:bg-navy-700 text-white text-md font-medium transition-colors disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
              {!loading && <ArrowRight className="w-4 h-4" />}
            </button>
          </div>
        </form>

        {/* Demo credentials */}
        <div className="mt-4 p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border)] text-sm text-[var(--text-tertiary)]">
          <p className="font-medium text-[var(--text-secondary)] mb-1">Demo credentials</p>
          <p>sarah@resolveai.demo / demo123</p>
        </div>
      </div>
    </div>
  );
}
