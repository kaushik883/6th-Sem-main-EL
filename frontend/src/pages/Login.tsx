import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Zap, AlertCircle, Eye, EyeOff, ChevronDown, Shield, Building2, Truck, User } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type FormData = z.infer<typeof schema>;

const TEST_ACCOUNTS = [
  {
    label: 'Super Admin',
    email: 'super_admin@logisight.dev',
    password: 'TestPass123!',
    description: 'Platform-wide access, manages all companies',
    icon: Shield,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20 hover:bg-amber-500/15',
  },
  {
    label: 'Client Admin',
    email: 'client.admin@acmeco.dev',
    password: 'TestPass123!',
    description: 'AcmeCo Logistics — admin access',
    icon: Building2,
    color: 'text-indigo-400',
    bg: 'bg-indigo-500/10 border-indigo-500/20 hover:bg-indigo-500/15',
  },
  {
    label: 'Client User',
    email: 'client.user@acmeco.dev',
    password: 'TestPass123!',
    description: 'AcmeCo Logistics — standard access',
    icon: User,
    color: 'text-indigo-300',
    bg: 'bg-indigo-500/8 border-indigo-500/15 hover:bg-indigo-500/12',
  },
  {
    label: 'Forwarder Admin',
    email: 'fwd.admin@fastfreight.dev',
    password: 'TestPass123!',
    description: 'FastFreight Co — admin access',
    icon: Truck,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500/15',
  },
  {
    label: 'Forwarder User',
    email: 'fwd.user@fastfreight.dev',
    password: 'TestPass123!',
    description: 'FastFreight Co — standard access',
    icon: User,
    color: 'text-emerald-300',
    bg: 'bg-emerald-500/8 border-emerald-500/15 hover:bg-emerald-500/12',
  },
];

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devOpen, setDevOpen] = useState(false);
  const [quickLoading, setQuickLoading] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormData) => {
    setError(null);
    try {
      await login(data.email, data.password);
      navigate('/app');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please try again.';
      setError(msg);
    }
  };

  const quickLogin = async (email: string, password: string) => {
    setError(null);
    setQuickLoading(email);
    try {
      await login(email, password);
      navigate('/app');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed.';
      setError(msg);
    } finally {
      setQuickLoading(null);
    }
  };

  const fillCredentials = (email: string, password: string) => {
    setValue('email', email);
    setValue('password', password);
  };

  return (
    <div className="min-h-screen flex" style={{ background: '#030712' }}>

      {/* ── Left panel ───────────────────────────────────────────────────────── */}
      <div className="hidden lg:flex flex-1 flex-col justify-between p-12 border-r border-white/[0.06] relative overflow-hidden">
        {/* Background glow */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-20 -left-20 w-96 h-96 rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.10) 0%, transparent 70%)' }}
          />
          <div className="absolute bottom-20 right-0 w-80 h-80 rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%, transparent 70%)' }}
          />
        </div>

        <Link to="/" className="relative flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg text-slate-100">
            Logi<span className="text-indigo-400">Sight</span>
          </span>
        </Link>

        <div className="relative max-w-sm">
          <div className="mb-6 w-10 h-1 rounded-full bg-gradient-to-r from-indigo-500 to-violet-500" />
          <blockquote className="text-xl font-medium text-slate-200 leading-relaxed mb-6">
            "We eliminated three hours of manual freight reconciliation every week in the first month."
          </blockquote>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center text-white font-bold text-sm shadow-lg">
              SL
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-200">Sarah L.</p>
              <p className="text-xs text-slate-500">Head of Procurement, Asia-Pacific</p>
            </div>
          </div>
        </div>

        <p className="relative text-xs text-slate-700">&copy; {new Date().getFullYear()} LogiSight</p>
      </div>

      {/* ── Right panel ──────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 overflow-y-auto">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-10">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-slate-100">
              Logi<span className="text-indigo-400">Sight</span>
            </span>
          </div>

          <h1 className="text-2xl font-bold text-slate-100 mb-1">Welcome back</h1>
          <p className="text-sm text-slate-400 mb-8">Sign in to your account to continue</p>

          {error && (
            <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 mb-6">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Email address
              </label>
              <input
                {...register('email')}
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                className="w-full px-3.5 py-2.5 rounded-xl border border-white/[0.08] bg-white/[0.04] text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30 transition-all"
              />
              {errors.email && (
                <p className="mt-1.5 text-xs text-red-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 pr-11 rounded-xl border border-white/[0.08] bg-white/[0.04] text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1.5 text-xs text-red-400">{errors.password.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold text-sm transition-all shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in…
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          {/* Dev Quick Login */}
          <div className="mt-8">
            <button
              type="button"
              onClick={() => setDevOpen((v) => !v)}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-dashed border-white/[0.10] text-slate-500 hover:border-indigo-500/30 hover:text-slate-400 transition-all text-xs font-medium"
            >
              <span>Dev — Quick Login</span>
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform duration-200 ${devOpen ? 'rotate-180' : ''}`}
              />
            </button>

            {devOpen && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-slate-600 mb-3">
                  All accounts use password: <span className="font-mono text-slate-500">TestPass123!</span>
                </p>
                {TEST_ACCOUNTS.map((acc) => {
                  const Icon = acc.icon;
                  const isLoading = quickLoading === acc.email;
                  return (
                    <div
                      key={acc.email}
                      className={`flex items-center gap-3 p-2.5 rounded-xl border cursor-pointer transition-all ${acc.bg}`}
                      onClick={() => !quickLoading && quickLogin(acc.email, acc.password)}
                    >
                      <div className="flex-shrink-0">
                        <Icon className={`w-4 h-4 ${acc.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-semibold ${acc.color}`}>{acc.label}</p>
                        <p className="text-xs text-slate-500 truncate">{acc.description}</p>
                      </div>
                      <div className="flex-shrink-0 flex items-center gap-2">
                        {isLoading ? (
                          <span className="w-3.5 h-3.5 border-2 border-slate-600 border-t-indigo-400 rounded-full animate-spin" />
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                fillCredentials(acc.email, acc.password);
                              }}
                              className="text-slate-600 hover:text-slate-400 text-xs transition-colors px-1"
                              title="Fill credentials"
                            >
                              Fill
                            </button>
                            <span className="text-slate-700 text-xs">|</span>
                            <span className="text-slate-600 text-xs">Login</span>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <p className="mt-6 text-center text-xs text-slate-500">
            Platform access is by invitation only.{' '}
            <Link to="/" className="text-indigo-400 hover:text-indigo-300 transition-colors">
              Learn more
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
