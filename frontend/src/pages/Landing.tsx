import { Link } from 'react-router-dom';
import {
  Zap,
  ArrowRight,
  CheckCircle2,
  FileSearch,
  GitMerge,
  BarChart3,
  MessageSquare,
  ShieldCheck,
  TrendingUp,
  Users,
  Globe,
  ChevronRight,
} from 'lucide-react';

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Forwarder Submits Quote',
    desc: 'Freight forwarders submit quotes using their own charge terminology — no need to learn your internal naming.',
    color: 'text-indigo-400',
    border: 'border-indigo-500/20',
    bg: 'bg-indigo-500/5',
    dot: 'bg-indigo-400',
  },
  {
    step: '02',
    title: 'AI Maps to Charge Master',
    desc: 'A three-tier pipeline (synonym dictionary → vector similarity → LLM fallback) maps every charge to your internal standard.',
    color: 'text-violet-400',
    border: 'border-violet-500/20',
    bg: 'bg-violet-500/5',
    dot: 'bg-violet-400',
  },
  {
    step: '03',
    title: 'Client Reviews & Accepts',
    desc: 'You see quotes in your own nomenclature. Low-confidence mappings are surfaced for one-click correction.',
    color: 'text-emerald-400',
    border: 'border-emerald-500/20',
    bg: 'bg-emerald-500/5',
    dot: 'bg-emerald-400',
  },
  {
    step: '04',
    title: 'Invoice Uploaded & Analysed',
    desc: 'The forwarder uploads the PDF invoice. OCR extraction + the same mapping pipeline runs automatically.',
    color: 'text-amber-400',
    border: 'border-amber-500/20',
    bg: 'bg-amber-500/5',
    dot: 'bg-amber-400',
  },
  {
    step: '05',
    title: 'Anomalies Flagged',
    desc: 'Amount mismatches, rate changes, unexpected charges, and duplicates are detected and surfaced instantly.',
    color: 'text-rose-400',
    border: 'border-rose-500/20',
    bg: 'bg-rose-500/5',
    dot: 'bg-rose-400',
  },
  {
    step: '06',
    title: 'Copilot Answers Questions',
    desc: 'Ask plain English questions about your freight spend. LogiSight translates to SQL and returns precise answers.',
    color: 'text-cyan-400',
    border: 'border-cyan-500/20',
    bg: 'bg-cyan-500/5',
    dot: 'bg-cyan-400',
  },
];

const ROLES = [
  {
    title: 'For Buyers & Importers',
    subtitle: 'Take control of your freight spend',
    Icon: ShieldCheck,
    color: 'text-emerald-400',
    border: 'border-emerald-500/20',
    bg: 'bg-emerald-500/5',
    points: [
      'Receive quotes mapped to your Charge Master automatically',
      'Review low-confidence mappings with one-click correction',
      'Accept or reject quotes with optional notes to forwarders',
      'Compare every invoice charge against the approved quote',
      'Get anomaly flags on mismatches, unexpected charges, and duplicates',
      'Query your entire freight history in plain English via Copilot',
    ],
  },
  {
    title: 'For Freight Forwarders',
    subtitle: 'Submit quotes and invoices your way',
    Icon: Globe,
    color: 'text-indigo-400',
    border: 'border-indigo-500/20',
    bg: 'bg-indigo-500/5',
    points: [
      'Use your own charge terminology — no mapping required on your end',
      'Submit structured quotes with dynamic charge lines',
      'Track quote status and read rejection notes in real time',
      'Upload PDF invoices directly against accepted quotes',
      'Clean, simple interface — no freight audit complexity exposed',
    ],
  },
  {
    title: 'For Platform Administrators',
    subtitle: 'Full control over the platform',
    Icon: Users,
    color: 'text-amber-400',
    border: 'border-amber-500/20',
    bg: 'bg-amber-500/5',
    points: [
      'Create and manage client and forwarder companies',
      'Provision first admin users for each company',
      'Activate or deactivate companies at any time',
      'Cross-company visibility for platform-level oversight',
      'Single database, multi-tenant architecture',
    ],
  },
];

const FEATURES = [
  { Icon: FileSearch, title: 'Veryfi OCR Extraction', desc: 'Purpose-built freight invoice extraction from any PDF format.' },
  { Icon: GitMerge, title: 'Three-Tier Mapping', desc: 'Synonym dictionary, vector similarity, and LLM fallback for near-100% accuracy.' },
  { Icon: BarChart3, title: 'Anomaly Detection', desc: 'Six flag types including amount mismatch, unexpected charges, and duplicates.' },
  { Icon: MessageSquare, title: 'LangChain Copilot', desc: 'Natural language to SQL — ask any question about your freight data.' },
  { Icon: TrendingUp, title: 'Audit Dashboard', desc: 'Charge-level comparison table with confidence badges and anomaly flags.' },
  { Icon: ShieldCheck, title: 'Role-Based Access', desc: 'Strict data isolation — forwarders never see your internal Charge Master.' },
];

export function Landing() {
  return (
    <div className="min-h-screen text-slate-100" style={{ background: '#030712' }}>

      {/* ── Nav ─────────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-white/[0.06]"
        style={{ background: 'rgba(3,7,18,0.85)', backdropFilter: 'blur(16px)' }}
      >
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">
              Logi<span className="text-indigo-400">Sight</span>
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm text-slate-400 hover:text-slate-100 transition-colors">
              Sign in
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-500/25"
            >
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-28 px-6 overflow-hidden">
        {/* Background glows */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] rounded-full"
            style={{ background: 'radial-gradient(ellipse at center top, rgba(99,102,241,0.12) 0%, transparent 70%)' }}
          />
          <div className="absolute top-20 left-1/2 -translate-x-[60%] w-[600px] h-[300px] bg-violet-600/5 rounded-full blur-3xl" />
          <div className="absolute top-32 left-1/2 translate-x-[10%] w-[400px] h-[200px] bg-indigo-600/6 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            AI-Powered Freight Audit Intelligence
          </div>

          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6 leading-[1.08]">
            Stop Overpaying on
            <br />
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
              Freight Invoices
            </span>
          </h1>

          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed mb-10">
            LogiSight automatically maps forwarder charge names to your internal standards,
            detects anomalies at the charge level, and lets you interrogate your entire
            freight spend in plain English.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-xl shadow-indigo-500/25"
            >
              Start Free Trial <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl border border-white/[0.10] hover:border-white/[0.20] text-slate-300 hover:text-white font-medium transition-all"
            >
              See How It Works
            </a>
          </div>

          <div className="mt-16 grid grid-cols-3 gap-8 max-w-lg mx-auto">
            {[
              { label: 'Mapping Accuracy', value: '99%+' },
              { label: 'Avg. Time Saved', value: '12h/mo' },
              { label: 'Anomaly Types', value: '6+' },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <p className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">{value}</p>
                <p className="text-xs text-slate-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6 border-t border-white/[0.05]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              From quote submission to anomaly detection — fully automated, end to end.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {HOW_IT_WORKS.map(({ step, title, desc, color, border, bg }) => (
              <div key={step} className={`relative p-6 rounded-2xl border ${border} ${bg} flex flex-col gap-3 hover:border-opacity-40 transition-all`}>
                <span className={`text-[10px] font-mono font-bold uppercase tracking-widest ${color} opacity-50`}>STEP {step}</span>
                <div className="flex items-start gap-3">
                  <ChevronRight className={`w-5 h-5 mt-0.5 flex-shrink-0 ${color}`} />
                  <div>
                    <h3 className="font-semibold text-slate-100 mb-1">{title}</h3>
                    <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Built for Your Role ───────────────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-white/[0.05]" style={{ background: 'rgba(255,255,255,0.01)' }}>
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Built for Your Role</h2>
            <p className="text-slate-400">Different personas, different needs — all served precisely.</p>
          </div>
          <div className="grid lg:grid-cols-3 gap-5">
            {ROLES.map(({ title, subtitle, Icon, color, border, bg, points }) => (
              <div key={title} className={`p-6 rounded-2xl border ${border} ${bg}`}>
                <div className="flex items-center gap-3 mb-5">
                  <div className={`w-10 h-10 rounded-xl border ${border} flex items-center justify-center`} style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <Icon className={`w-5 h-5 ${color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-100">{title}</h3>
                    <p className={`text-xs mt-0.5 ${color}`}>{subtitle}</p>
                  </div>
                </div>
                <ul className="space-y-2.5">
                  {points.map((p) => (
                    <li key={p} className="flex items-start gap-2.5">
                      <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${color}`} />
                      <span className="text-sm text-slate-300">{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Platform Capabilities ─────────────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-white/[0.05]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Platform Capabilities</h2>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(({ Icon, title, desc }) => (
              <div key={title} className="p-5 rounded-2xl border border-white/[0.07] bg-white/[0.02] flex gap-4 hover:border-indigo-500/25 hover:bg-indigo-500/5 transition-all group">
                <div className="w-10 h-10 rounded-xl border border-indigo-500/20 bg-indigo-500/10 flex items-center justify-center flex-shrink-0 group-hover:border-indigo-500/40 transition-all">
                  <Icon className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-100 mb-1">{title}</h3>
                  <p className="text-sm text-slate-400">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────────── */}
      <section className="py-24 px-6 border-t border-white/[0.05]">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to audit smarter?</h2>
          <p className="text-slate-400 mb-8">
            Join logistics teams already saving hours on freight reconciliation every month.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-all shadow-xl shadow-indigo-500/25"
          >
            Get Started Now <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.05] py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center">
              <Zap className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-bold text-slate-300">
              Logi<span className="text-indigo-400">Sight</span>
            </span>
          </div>
          <p className="text-xs text-slate-600">
            &copy; {new Date().getFullYear()} LogiSight. AI-Powered Freight Audit Intelligence.
          </p>
        </div>
      </footer>
    </div>
  );
}
