import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Upload,
  BookOpen,
  MapPin,
  MessageSquare,
  Building2,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Zap,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface NavItem {
  to: string;
  label: string;
  Icon: React.ElementType;
}

const SUPER_ADMIN_NAV: NavItem[] = [
  { to: '/app', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/app/companies', label: 'Companies', Icon: Building2 },
];

const CLIENT_NAV: NavItem[] = [
  { to: '/app', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/app/quotes', label: 'Quotes', Icon: FileText },
  { to: '/app/invoices', label: 'Invoices', Icon: Upload },
  { to: '/app/charge-master', label: 'Charge Master', Icon: BookOpen },
  { to: '/app/tracking', label: 'Tracking', Icon: MapPin },
  { to: '/app/copilot', label: 'Copilot', Icon: MessageSquare },
];

const FORWARDER_NAV: NavItem[] = [
  { to: '/app', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/app/quotes', label: 'Quotes', Icon: FileText },
  { to: '/app/invoices', label: 'Invoices', Icon: Upload },
  { to: '/app/tracking', label: 'Tracking', Icon: MapPin },
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const nav =
    user?.role === 'super_admin'
      ? SUPER_ADMIN_NAV
      : user?.role === 'forwarder'
      ? FORWARDER_NAV
      : CLIENT_NAV;

  const rolePill =
    user?.role === 'super_admin'
      ? { label: 'Super Admin', cls: 'bg-violet-500/15 text-violet-300 border-violet-500/25' }
      : user?.role === 'forwarder'
      ? { label: 'Forwarder', cls: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/25' }
      : { label: 'Client', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25' };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => (
    <div
      className={`flex flex-col h-full border-r border-white/[0.06] transition-all duration-200 ${
        mobile ? 'w-64' : collapsed ? 'w-16' : 'w-60'
      }`}
      style={{
        background: 'linear-gradient(180deg, #0a0a1a 0%, #06060f 100%)',
      }}
    >
      {/* Logo */}
      <div className={`flex items-center gap-3 px-4 py-5 border-b border-white/[0.06] ${collapsed && !mobile ? 'justify-center' : ''}`}>
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-indigo-500/30">
          <Zap className="w-4 h-4 text-white" />
        </div>
        {(!collapsed || mobile) && (
          <span className="text-slate-100 font-bold text-base tracking-tight">
            Logi<span className="text-indigo-400">Sight</span>
          </span>
        )}
        {!mobile && (
          <button
            onClick={() => setCollapsed((v) => !v)}
            className="ml-auto w-6 h-6 rounded-lg flex items-center justify-center text-slate-600 hover:text-slate-300 hover:bg-white/[0.06] transition-all"
          >
            {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-0.5 px-2">
          {nav.map(({ to, label, Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/app'}
                onClick={() => mobile && setMobileOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    collapsed && !mobile ? 'justify-center' : ''
                  } ${
                    isActive
                      ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/25 shadow-sm'
                      : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.05] border border-transparent'
                  }`
                }
                title={collapsed && !mobile ? label : undefined}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {(!collapsed || mobile) && <span>{label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User footer */}
      <div className={`px-2 py-3 border-t border-white/[0.06] ${collapsed && !mobile ? 'items-center flex flex-col' : ''}`}>
        {(!collapsed || mobile) && (
          <div className="px-3 py-2.5 mb-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <p className="text-sm font-semibold text-slate-200 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 truncate mt-0.5">{user?.company_name}</p>
            <span className={`mt-2 inline-block px-2 py-0.5 rounded-full border text-xs font-medium ${rolePill.cls}`}>
              {rolePill.label}
            </span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={`flex items-center gap-2 px-3 py-2 w-full rounded-xl text-sm text-slate-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-all ${
            collapsed && !mobile ? 'justify-center' : ''
          }`}
          title={collapsed && !mobile ? 'Sign out' : undefined}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {(!collapsed || mobile) && <span>Sign out</span>}
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#030712' }}>
      {/* Desktop sidebar */}
      <div className="hidden md:flex h-full flex-shrink-0">
        <Sidebar />
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative h-full">
            <Sidebar mobile />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b border-white/[0.06] flex items-center px-4 gap-3 flex-shrink-0"
          style={{ background: 'rgba(3,7,18,0.85)', backdropFilter: 'blur(12px)' }}
        >
          <button
            onClick={() => setMobileOpen(true)}
            className="md:hidden text-slate-400 hover:text-slate-200"
          >
            <Menu className="w-5 h-5" />
          </button>
          {mobileOpen && (
            <button onClick={() => setMobileOpen(false)} className="md:hidden text-slate-400">
              <X className="w-5 h-5" />
            </button>
          )}
          {/* Subtle top-bar gradient accent */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
        </header>

        <main className="flex-1 overflow-y-auto">
          {/* Ambient background glow */}
          <div className="pointer-events-none fixed inset-0 overflow-hidden">
            <div className="absolute -top-40 left-1/4 w-96 h-96 bg-indigo-600/5 rounded-full blur-3xl" />
            <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-violet-600/4 rounded-full blur-3xl" />
          </div>
          <div className="relative max-w-7xl mx-auto px-4 md:px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
