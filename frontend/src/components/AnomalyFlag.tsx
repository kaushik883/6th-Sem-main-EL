import { AlertTriangle, XCircle, MinusCircle, Copy, TrendingUp, ArrowUpDown, Weight, Thermometer } from 'lucide-react';
import type { AnomalyFlagType } from '../api/types';

interface Props {
  flagType: AnomalyFlagType;
  description?: string;
  compact?: boolean;
}

const CONFIG: Record<
  AnomalyFlagType,
  {
    label: string;
    sublabel: string;
    iconBg: string;
    iconColor: string;
    border: string;
    bg: string;
    badge: string;
    badgeText: string;
    Icon: React.ElementType;
  }
> = {
  AMOUNT_MISMATCH: {
    label: 'Amount Mismatch',
    sublabel: 'Charge total differs from quoted amount',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    border: 'border-amber-500/20',
    bg: 'bg-amber-950/20',
    badge: 'bg-amber-500/15 border-amber-500/30',
    badgeText: 'text-amber-300',
    Icon: TrendingUp,
  },
  RATE_MISMATCH: {
    label: 'Rate Mismatch',
    sublabel: 'Applied rate deviates from the quote',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    border: 'border-amber-500/20',
    bg: 'bg-amber-950/20',
    badge: 'bg-amber-500/15 border-amber-500/30',
    badgeText: 'text-amber-300',
    Icon: ArrowUpDown,
  },
  BASIS_MISMATCH: {
    label: 'Basis Mismatch',
    sublabel: 'Charge basis changed between quote and invoice',
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-400',
    border: 'border-amber-500/20',
    bg: 'bg-amber-950/20',
    badge: 'bg-amber-500/15 border-amber-500/30',
    badgeText: 'text-amber-300',
    Icon: AlertTriangle,
  },
  UNEXPECTED_CHARGE: {
    label: 'Unexpected Charge',
    sublabel: 'Line item not present in the original quote',
    iconBg: 'bg-red-500/10',
    iconColor: 'text-red-400',
    border: 'border-red-500/20',
    bg: 'bg-red-950/20',
    badge: 'bg-red-500/15 border-red-500/30',
    badgeText: 'text-red-300',
    Icon: XCircle,
  },
  MISSING_CHARGE: {
    label: 'Missing Charge',
    sublabel: 'Quoted line item absent from invoice',
    iconBg: 'bg-slate-600/30',
    iconColor: 'text-slate-400',
    border: 'border-slate-600/30',
    bg: 'bg-slate-800/30',
    badge: 'bg-slate-600/20 border-slate-600/40',
    badgeText: 'text-slate-400',
    Icon: MinusCircle,
  },
  DUPLICATE_INVOICE: {
    label: 'Duplicate Invoice',
    sublabel: 'Invoice number already exists in the system',
    iconBg: 'bg-red-500/10',
    iconColor: 'text-red-400',
    border: 'border-red-500/20',
    bg: 'bg-red-950/20',
    badge: 'bg-red-500/15 border-red-500/30',
    badgeText: 'text-red-300',
    Icon: Copy,
  },
  TELEMETRY_WEIGHT_DROP: {
    label: 'Cargo Weight Drop',
    sublabel: 'Sudden weight loss detected in sensor readings',
    iconBg: 'bg-orange-500/10',
    iconColor: 'text-orange-400',
    border: 'border-orange-500/20',
    bg: 'bg-orange-950/20',
    badge: 'bg-orange-500/15 border-orange-500/30',
    badgeText: 'text-orange-300',
    Icon: Weight,
  },
  SLA_TEMP_BREACH: {
    label: 'Temperature SLA Breach',
    sublabel: 'Cold-chain threshold exceeded for 2+ consecutive hours',
    iconBg: 'bg-rose-500/10',
    iconColor: 'text-rose-400',
    border: 'border-rose-500/20',
    bg: 'bg-rose-950/20',
    badge: 'bg-rose-500/15 border-rose-500/30',
    badgeText: 'text-rose-300',
    Icon: Thermometer,
  },
};

export function AnomalyFlag({ flagType, description, compact = false }: Props) {
  const c = CONFIG[flagType];
  const Icon = c.Icon;

  if (compact) {
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-xs font-semibold ${c.badge} ${c.badgeText}`}>
        <Icon className="w-3 h-3" />
        {c.label}
      </span>
    );
  }

  return (
    <div className={`flex items-start gap-4 p-4 rounded-2xl border ${c.border} ${c.bg} transition-all duration-200 hover:brightness-110`}>
      <div className={`flex-shrink-0 p-2.5 rounded-xl border ${c.iconBg} ${c.border}`}>
        <Icon className={`w-4 h-4 ${c.iconColor}`} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className={`text-sm font-semibold ${c.iconColor}`}>{c.label}</p>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-widest border ${c.badge} ${c.badgeText}`}>
            {flagType.replace(/_/g, ' ')}
          </span>
        </div>
        {description && (
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{description}</p>
        )}
      </div>
    </div>
  );
}
