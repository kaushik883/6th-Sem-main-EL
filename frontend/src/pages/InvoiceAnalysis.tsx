import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft, Zap, AlertTriangle, CheckCircle2, FileText,
  ExternalLink, Activity, TrendingUp, ShieldAlert, BarChart3
} from 'lucide-react';
import { getInvoice, analyzeInvoice, getAnomalies, getCharges, correctInvoiceChargeMapping, getQuote } from '../api/client';
import { ChargeLineTable } from '../components/ChargeLineTable';
import { AnomalyFlag } from '../components/AnomalyFlag';
import TelemetryDashboard from '../components/TelemetryDashboard';
import { useAuth } from '../hooks/useAuth';

const TELEMETRY_FLAG_TYPES = new Set(['TELEMETRY_WEIGHT_DROP', 'SLA_TEMP_BREACH']);

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Section wrapper with consistent heading style ─────────────────────────────
function Section({
  icon: Icon,
  title,
  badge,
  iconColor = 'text-slate-400',
  children,
}: {
  icon: React.ElementType;
  title: string;
  badge?: React.ReactNode;
  iconColor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2.5">
        <div className={`p-1.5 rounded-md bg-slate-800/80 border border-slate-700/60`}>
          <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
        </div>
        <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">
          {title}
        </h2>
        {badge}
      </div>
      {children}
    </div>
  );
}

// ── Stat card for variance summary ────────────────────────────────────────────
function StatCard({
  label, value, accent = false, positive = false,
}: {
  label: string; value: string; accent?: boolean; positive?: boolean;
}) {
  const borderColor = accent
    ? positive ? 'border-emerald-500/30' : 'border-red-500/30'
    : 'border-slate-700/60';
  const bgColor = accent
    ? positive ? 'bg-emerald-950/30' : 'bg-red-950/30'
    : 'bg-slate-800/40';
  const valueColor = accent
    ? positive ? 'text-emerald-400' : 'text-red-400'
    : 'text-slate-100';

  return (
    <div className={`rounded-2xl border ${borderColor} ${bgColor} p-5 backdrop-blur-sm`}>
      <p className="text-[11px] font-medium text-slate-500 uppercase tracking-widest mb-2">{label}</p>
      <p className={`text-2xl font-bold font-mono ${valueColor} tabular-nums`}>{value}</p>
    </div>
  );
}

export function InvoiceAnalysis() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { user } = useAuth();
  const isClient = user?.role === 'client';

  const [analysed, setAnalysed] = useState(false);

  const { data: invoice, isLoading: invLoading } = useQuery({
    queryKey: ['invoices', Number(id)],
    queryFn: () => getInvoice(Number(id)),
    enabled: !!id,
  });

  const { data: chargeMaster = [] } = useQuery({
    queryKey: ['charges'],
    queryFn: getCharges,
    enabled: isClient,
  });

  const { data: quoteDetail } = useQuery({
    queryKey: ['quotes', invoice?.quote_id],
    queryFn: () => getQuote(invoice!.quote_id),
    enabled: !!invoice?.quote_id && isClient,
  });

  const { data: anomalies = [], refetch: refetchAnomalies } = useQuery({
    queryKey: ['anomalies', Number(id)],
    queryFn: () => getAnomalies(Number(id)),
    enabled: analysed,
  });

  const analyseMutation = useMutation({
    mutationFn: () => analyzeInvoice(Number(id)),
    onSuccess: async () => {
      setAnalysed(true);
      await refetchAnomalies();
    },
  });

  const correctMutation = useMutation({
    mutationFn: ({ chargeId, mappedChargeId }: { chargeId: number; mappedChargeId: number }) =>
      correctInvoiceChargeMapping(chargeId, mappedChargeId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['invoices', Number(id)] }),
  });

  if (invLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-20 rounded-2xl border border-slate-800 bg-slate-900/40" />
        <div className="grid grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-24 rounded-2xl border border-slate-800 bg-slate-900/40" />)}
        </div>
        <div className="h-64 rounded-2xl border border-slate-800 bg-slate-900/40" />
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
        <FileText className="w-10 h-10 text-slate-600" />
        <p className="text-slate-400 font-medium">Invoice not found.</p>
      </div>
    );
  }

  const invoiceTotal = (invoice.charges ?? []).reduce((s, c) => s + c.amount, 0);
  const quoteTotal   = (quoteDetail?.charges ?? []).reduce((s, c) => s + c.amount, 0);
  const variance     = invoiceTotal - quoteTotal;

  const financialAnomalies = anomalies.filter((a) => !TELEMETRY_FLAG_TYPES.has(a.flag_type));
  const telemetryAnomalies = anomalies.filter((a) =>  TELEMETRY_FLAG_TYPES.has(a.flag_type));
  const telemetryData      = (quoteDetail as any)?.telemetry_data ?? [];

  const totalFlags = anomalies.length;

  return (
    <div className="space-y-8">

      {/* ── Page Header ────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => navigate('/app/invoices')}
          className="mt-1 p-2 rounded-xl border border-slate-700/60 bg-slate-800/40 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-2xl font-bold text-slate-100 font-mono tracking-tight">
                {invoice.invoice_number}
              </h1>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 text-xs font-mono">
                  {invoice.quote?.quote_ref}
                </span>
                <span className="text-slate-600 text-xs">·</span>
                <span className="text-slate-500 text-xs">{invoice.invoice_date}</span>
                {analysed && totalFlags > 0 && (
                  <>
                    <span className="text-slate-600 text-xs">·</span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-semibold">
                      <ShieldAlert className="w-3 h-3" />
                      {totalFlags} flag{totalFlags > 1 ? 's' : ''} detected
                    </span>
                  </>
                )}
                {analysed && totalFlags === 0 && (
                  <>
                    <span className="text-slate-600 text-xs">·</span>
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                      <CheckCircle2 className="w-3 h-3" />
                      Clean
                    </span>
                  </>
                )}
              </div>
            </div>

            {isClient && (
              <button
                onClick={() => analyseMutation.mutate()}
                disabled={analyseMutation.isPending}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 active:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-all shadow-lg shadow-sky-500/25 hover:shadow-sky-400/30"
              >
                <Zap className={`w-4 h-4 ${analyseMutation.isPending ? 'animate-pulse' : ''}`} />
                {analyseMutation.isPending ? 'Analysing…' : 'Analyse Invoice'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Variance Summary ───────────────────────────────────────────────── */}
      {isClient && analysed && quoteDetail && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Invoice Total" value={fmt(invoiceTotal)} />
          <StatCard label="Quoted Total"  value={fmt(quoteTotal)} />
          <StatCard
            label="Net Variance"
            value={`${variance >= 0 ? '+' : ''}${fmt(variance)}`}
            accent
            positive={variance <= 0}
          />
        </div>
      )}

      {/* ── Telemetry Forensics ────────────────────────────────────────────── */}
      {isClient && analysed && (
        <Section
          icon={Activity}
          title="Virtual Telemetry Forensics"
          iconColor="text-violet-400"
          badge={
            telemetryAnomalies.length > 0 ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-red-500/15 border border-red-500/30 text-red-300 text-xs font-semibold animate-pulse">
                {telemetryAnomalies.length} flag{telemetryAnomalies.length > 1 ? 's' : ''}
              </span>
            ) : telemetryData.length > 0 ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="w-3 h-3" /> Clear
              </span>
            ) : null
          }
        >
          {telemetryData.length > 0 ? (
            <TelemetryDashboard
              telemetryData={telemetryData}
              anomalies={telemetryAnomalies}
              tempThreshold={5}
            />
          ) : (
            <div className="flex items-center gap-4 px-5 py-4 rounded-2xl border border-slate-700/60 bg-slate-800/30">
              <div className="p-2.5 rounded-xl bg-slate-700/40 border border-slate-600/40">
                <Activity className="w-4 h-4 text-slate-500" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-300">No sensor data available</p>
                <p className="text-xs text-slate-500 mt-0.5">Telemetry is generated when a quote is accepted.</p>
              </div>
            </div>
          )}
        </Section>
      )}

      {/* ── Financial Anomalies ────────────────────────────────────────────── */}
      {isClient && analysed && (
        <Section
          icon={AlertTriangle}
          title="Financial Anomalies"
          iconColor="text-amber-400"
          badge={
            financialAnomalies.length > 0 ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                {financialAnomalies.length} detected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                <CheckCircle2 className="w-3 h-3" /> Clear
              </span>
            )
          }
        >
          {financialAnomalies.length > 0 ? (
            <div className="grid gap-2.5">
              {financialAnomalies.map((a) => (
                <AnomalyFlag key={a.id} flagType={a.flag_type} description={a.description} />
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-4 px-5 py-4 rounded-2xl border border-emerald-500/20 bg-emerald-950/20">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-emerald-300">All charges verified</p>
                <p className="text-xs text-emerald-500/70 mt-0.5">Invoice charges match the accepted quote.</p>
              </div>
            </div>
          )}
        </Section>
      )}

      {/* ── Charge Table ──────────────────────────────────────────────────── */}
      <Section
        icon={BarChart3}
        title="Invoice Charges"
        iconColor="text-sky-400"
        badge={
          isClient ? (
            <span className="text-xs text-slate-500 font-normal normal-case tracking-normal">
              {analysed && quoteDetail ? 'charge-wise variance shown' : 'mapped to your Charge Master'}
            </span>
          ) : undefined
        }
      >
        <ChargeLineTable
          charges={invoice.charges ?? []}
          isClient={isClient}
          showConfidence={isClient}
          chargeMaster={chargeMaster}
          onCorrectMapping={
            isClient
              ? (chargeId, mappedChargeId) =>
                  correctMutation.mutate({ chargeId, mappedChargeId })
              : undefined
          }
          anomalies={isClient && analysed ? anomalies : []}
          quoteCharges={isClient && analysed && quoteDetail ? (quoteDetail.charges ?? []) : []}
        />
      </Section>

      {/* ── PDF Source Document ───────────────────────────────────────────── */}
      <a
        href={invoice.file_path}
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-4 w-full px-5 py-4 rounded-2xl border border-slate-700/60 bg-slate-800/30 hover:bg-slate-800/60 hover:border-slate-600 transition-all group"
      >
        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
          <FileText className="w-4 h-4 text-red-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-200 truncate">{invoice.invoice_number}.pdf</p>
          <p className="text-xs text-slate-500 mt-0.5">Source document · Click to open in a new tab</p>
        </div>
        <ExternalLink className="w-4 h-4 text-slate-600 group-hover:text-slate-300 transition-colors flex-shrink-0" />
      </a>

    </div>
  );
}
