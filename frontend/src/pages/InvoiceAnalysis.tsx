import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Zap, AlertTriangle, CheckCircle2, FileText, ExternalLink } from 'lucide-react';
import { getInvoice, analyzeInvoice, getAnomalies, getCharges, correctInvoiceChargeMapping, getQuote } from '../api/client';
import { ChargeLineTable } from '../components/ChargeLineTable';
import { AnomalyFlag } from '../components/AnomalyFlag';
import { useAuth } from '../hooks/useAuth';

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
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
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 rounded-xl border border-slate-800 bg-slate-900/40 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!invoice) {
    return <div className="text-slate-400 py-12 text-center">Invoice not found.</div>;
  }

  const invoiceTotal = (invoice.charges ?? []).reduce((s, c) => s + c.amount, 0);
  const quoteTotal = (quoteDetail?.charges ?? []).reduce((s, c) => s + c.amount, 0);
  const variance = invoiceTotal - quoteTotal;

  return (
    <div className="space-y-6">

      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/app/invoices')}
          className="text-slate-500 hover:text-slate-300 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 font-mono">{invoice.invoice_number}</h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Quote: <span className="font-mono">{invoice.quote?.quote_ref}</span>
              {' · '}{invoice.invoice_date}
            </p>
          </div>
          {isClient && (
            <button
              onClick={() => analyseMutation.mutate()}
              disabled={analyseMutation.isPending}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 disabled:opacity-60 text-white text-sm font-semibold transition-colors shadow-lg shadow-sky-500/20"
            >
              <Zap className={`w-4 h-4 ${analyseMutation.isPending ? 'animate-pulse' : ''}`} />
              {analyseMutation.isPending ? 'Analysing…' : 'Analyse Invoice'}
            </button>
          )}
        </div>
      </div>

      {/* ── Variance Summary (client only, after analyse) ── */}
      {isClient && analysed && quoteDetail && (
        <div className="grid grid-cols-3 gap-3">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <p className="text-xs text-slate-500 mb-1">Invoice Total</p>
            <p className="text-xl font-bold font-mono text-slate-100">{fmt(invoiceTotal)}</p>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <p className="text-xs text-slate-500 mb-1">Quoted Total</p>
            <p className="text-xl font-bold font-mono text-slate-400">{fmt(quoteTotal)}</p>
          </div>
          <div className={`p-4 rounded-xl border ${variance > 0 ? 'border-red-800 bg-red-950/20' : variance < 0 ? 'border-emerald-800 bg-emerald-950/20' : 'border-slate-800 bg-slate-900/40'}`}>
            <p className="text-xs text-slate-500 mb-1">Net Variance</p>
            <p className={`text-xl font-bold font-mono ${variance > 0 ? 'text-red-400' : variance < 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
              {variance >= 0 ? '+' : ''}{fmt(variance)}
            </p>
          </div>
        </div>
      )}

      {/* ── Anomalies (client only, after analyse) ── */}
      {isClient && analysed && anomalies.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-semibold text-slate-200">
              {anomalies.length} Anomal{anomalies.length === 1 ? 'y' : 'ies'} Detected
            </h2>
          </div>
          <div className="grid gap-3">
            {anomalies.map((a) => (
              <AnomalyFlag key={a.id} flagType={a.flag_type} description={a.description} />
            ))}
          </div>
        </div>
      )}

      {isClient && analysed && anomalies.length === 0 && (
        <div className="flex items-center gap-3 p-4 rounded-lg border border-emerald-800 bg-emerald-950/20">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          <p className="text-sm text-emerald-300 font-medium">No anomalies detected — invoice matches the quote.</p>
        </div>
      )}

      {/* ── Charge Table ── */}
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-slate-200">
          Invoice Charges
          {isClient && (
            <span className="ml-2 text-xs font-normal text-slate-500">
              {analysed && quoteDetail ? '— charge-wise variance shown' : '— mapped to your Charge Master'}
            </span>
          )}
        </h2>
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
      </div>

      {/* ── PDF Strip at bottom ── */}
      <a
        href={invoice.file_path}
        target="_blank"
        rel="noreferrer"
        className="flex items-center gap-4 w-full px-5 py-4 rounded-xl border border-slate-700 bg-slate-900/60 hover:bg-slate-800/60 hover:border-slate-500 transition-colors group"
      >
        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-950/40 border border-red-800/50 flex items-center justify-center">
          <FileText className="w-5 h-5 text-red-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-200 truncate">{invoice.invoice_number}.pdf</p>
          <p className="text-xs text-slate-500 mt-0.5">Click to open invoice PDF in a new tab</p>
        </div>
        <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors flex-shrink-0" />
      </a>

    </div>
  );
}
