/**
 * TelemetryDashboard.tsx
 * ======================
 * Virtual Telemetry Forensics visualisation panel for LogiSight.
 *
 * Renders two Recharts LineCharts:
 *   1. Weight (kg) over time — highlights the theft-induced drop.
 *   2. Temperature (°C) over time — shows SLA breaches with a red reference line.
 *
 * Props:
 *   telemetryData  – array of hourly sensor records from quotes.telemetry_data
 *   anomalies      – (optional) anomaly dicts returned by the /analyze endpoint
 *   title          – (optional) panel heading override
 */

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  Legend,
  Area,
  AreaChart,
} from "recharts";

// ── Types ────────────────────────────────────────────────────────────────────

export interface TelemetryRecord {
  timestamp: string;
  weight_kg: number;
  temp_c: number;
  gps_lat: number;
  gps_lon: number;
}

export interface TelemetryAnomaly {
  flag_type: "TELEMETRY_WEIGHT_DROP" | "SLA_TEMP_BREACH" | string;
  description: string;
  variance?: number;
  timestamp?: string;
  hour_index?: number;
}

interface TelemetryDashboardProps {
  telemetryData: TelemetryRecord[];
  anomalies?: TelemetryAnomaly[];
  title?: string;
  tempThreshold?: number; // °C SLA threshold line, default 5
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Format ISO timestamp to short "HH:00" label */
function fmtHour(iso: string): string {
  try {
    const d = new Date(iso);
    return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
  } catch {
    return iso;
  }
}

/** Custom tooltip for weight chart */
const WeightTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const val: number = payload[0]?.value;
  return (
    <div className="bg-slate-900/95 border border-slate-700 rounded-xl px-4 py-3 shadow-2xl backdrop-blur-sm">
      <p className="text-slate-400 text-xs mb-1">{label}</p>
      <p className="text-emerald-400 font-semibold text-sm">
        {val?.toFixed(2)} kg
      </p>
    </div>
  );
};

/** Custom tooltip for temperature chart */
const TempTooltip = ({ active, payload, label, threshold }: any) => {
  if (!active || !payload?.length) return null;
  const val: number = payload[0]?.value;
  const breach = val > threshold;
  return (
    <div className="bg-slate-900/95 border border-slate-700 rounded-xl px-4 py-3 shadow-2xl backdrop-blur-sm">
      <p className="text-slate-400 text-xs mb-1">{label}</p>
      <p
        className={`font-semibold text-sm ${
          breach ? "text-red-400" : "text-sky-400"
        }`}
      >
        {val?.toFixed(2)} °C{breach ? " ⚠ SLA BREACH" : ""}
      </p>
    </div>
  );
};

// ── Badge components ─────────────────────────────────────────────────────────

const FLAG_META: Record<string, { label: string; color: string; bg: string; icon: string }> = {
  TELEMETRY_WEIGHT_DROP: {
    label: "Weight Drop",
    color: "text-orange-300",
    bg: "bg-orange-500/15 border-orange-500/30",
    icon: "⚖️",
  },
  SLA_TEMP_BREACH: {
    label: "Temp Breach",
    color: "text-red-300",
    bg: "bg-red-500/15 border-red-500/30",
    icon: "🌡️",
  },
};

function AnomalyCard({ anomaly }: { anomaly: TelemetryAnomaly }) {
  const meta = FLAG_META[anomaly.flag_type] ?? {
    label: anomaly.flag_type,
    color: "text-slate-300",
    bg: "bg-slate-500/15 border-slate-500/30",
    icon: "🔍",
  };

  return (
    <div
      className={`flex gap-3 rounded-xl border p-4 ${meta.bg} transition-all duration-300 hover:scale-[1.01]`}
    >
      <span className="text-2xl">{meta.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-bold uppercase tracking-widest ${meta.color}`}>
            {meta.label}
          </span>
          {anomaly.variance !== undefined && (
            <span className="ml-auto text-xs font-mono text-slate-400">
              Δ {anomaly.variance > 0 ? "+" : ""}
              {anomaly.variance.toFixed(2)}
            </span>
          )}
        </div>
        <p className="text-slate-300 text-sm leading-relaxed">{anomaly.description}</p>
        {anomaly.timestamp && (
          <p className="text-slate-500 text-xs mt-1 font-mono">{anomaly.timestamp}</p>
        )}
      </div>
    </div>
  );
}

// ── Stats card ───────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  unit,
  sub,
  color,
}: {
  label: string;
  value: string | number;
  unit?: string;
  sub?: string;
  color?: string;
}) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 flex flex-col gap-1 hover:border-slate-600 transition-colors">
      <span className="text-slate-400 text-xs uppercase tracking-widest font-medium">
        {label}
      </span>
      <span className={`text-3xl font-bold tabular-nums ${color ?? "text-white"}`}>
        {value}
        {unit && <span className="text-base font-normal text-slate-400 ml-1">{unit}</span>}
      </span>
      {sub && <span className="text-slate-500 text-xs">{sub}</span>}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

const TelemetryDashboard: React.FC<TelemetryDashboardProps> = ({
  telemetryData,
  anomalies = [],
  title = "Virtual Telemetry Forensics",
  tempThreshold = 5,
}) => {
  // Derived chart data
  const chartData = useMemo(
    () =>
      telemetryData.map((r) => ({
        ...r,
        hour: fmtHour(r.timestamp),
      })),
    [telemetryData]
  );

  // Summary stats
  const weightValues = useMemo(
    () => telemetryData.map((r) => r.weight_kg),
    [telemetryData]
  );
  const tempValues = useMemo(
    () => telemetryData.map((r) => r.temp_c),
    [telemetryData]
  );

  const minWeight   = weightValues.length ? Math.min(...weightValues) : 0;
  const maxWeight   = weightValues.length ? Math.max(...weightValues) : 0;
  const weightDelta = maxWeight - minWeight;
  const maxTemp     = tempValues.length   ? Math.max(...tempValues)   : 0;
  const breachCount = tempValues.filter((t) => t > tempThreshold).length;

  const telemetryAnomalies = anomalies.filter(
    (a) =>
      a.flag_type === "TELEMETRY_WEIGHT_DROP" ||
      a.flag_type === "SLA_TEMP_BREACH"
  );

  if (!telemetryData || telemetryData.length === 0) {
    return (
      <div className="rounded-2xl bg-slate-900 border border-slate-700 p-10 text-center">
        <p className="text-4xl mb-3">📡</p>
        <p className="text-slate-400 font-medium">No telemetry data available for this shipment.</p>
        <p className="text-slate-600 text-sm mt-1">
          Run the simulator: <code className="text-slate-400">python scripts/generate_telemetry.py --quote_id &lt;ID&gt; --base_weight 500</code>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-sans">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <span className="text-2xl">🔬</span> {title}
          </h2>
          <p className="text-slate-400 text-sm mt-0.5">
            {telemetryData.length}h of E&amp;I sensor data · SLA threshold {tempThreshold}°C
          </p>
        </div>
        {telemetryAnomalies.length > 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/20 border border-red-500/40 px-4 py-1.5 text-red-300 text-sm font-semibold animate-pulse">
            <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
            {telemetryAnomalies.length} Forensic Flag{telemetryAnomalies.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* ── Stats row ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Max Weight"
          value={maxWeight.toFixed(1)}
          unit="kg"
          sub={`Min: ${minWeight.toFixed(1)} kg`}
          color="text-emerald-400"
        />
        <StatCard
          label="Weight Delta"
          value={weightDelta.toFixed(1)}
          unit="kg"
          sub={weightDelta > 10 ? "⚠ Significant variance" : "Within tolerance"}
          color={weightDelta > 10 ? "text-orange-400" : "text-slate-300"}
        />
        <StatCard
          label="Peak Temp"
          value={maxTemp.toFixed(1)}
          unit="°C"
          sub={`SLA threshold: ${tempThreshold}°C`}
          color={maxTemp > tempThreshold ? "text-red-400" : "text-sky-400"}
        />
        <StatCard
          label="Breach Hours"
          value={breachCount}
          unit="h"
          sub={`Above ${tempThreshold}°C SLA`}
          color={breachCount > 0 ? "text-red-400" : "text-slate-300"}
        />
      </div>

      {/* ── Weight Chart ───────────────────────────────────────────────── */}
      <div className="rounded-2xl bg-slate-800/50 border border-slate-700/60 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-white font-semibold flex items-center gap-2">
              <span>⚖️</span> Cargo Weight Monitor
            </h3>
            <p className="text-slate-500 text-xs mt-0.5">
              Moving-average anomaly detection · ±1 kg noise floor
            </p>
          </div>
          <span className="text-emerald-400 text-xs font-mono bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
            kg / hour
          </span>
        </div>

        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="weightGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#10b981" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="weightGradDrop" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="hour"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={["auto", "auto"]}
              tickFormatter={(v) => `${v} kg`}
              width={72}
            />
            <Tooltip content={<WeightTooltip />} />
            <Area
              type="monotone"
              dataKey="weight_kg"
              stroke="#10b981"
              strokeWidth={2.5}
              fill="url(#weightGrad)"
              dot={false}
              activeDot={{ r: 5, fill: "#10b981", strokeWidth: 0 }}
              name="Weight (kg)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ── Temperature Chart ──────────────────────────────────────────── */}
      <div className="rounded-2xl bg-slate-800/50 border border-slate-700/60 p-6 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="text-white font-semibold flex items-center gap-2">
              <span>🌡️</span> Cold-Chain Temperature Monitor
            </h3>
            <p className="text-slate-500 text-xs mt-0.5">
              Consecutive-hour breach detection · red line = SLA limit
            </p>
          </div>
          <span className="text-sky-400 text-xs font-mono bg-sky-500/10 border border-sky-500/20 px-3 py-1 rounded-full">
            °C / hour
          </span>
        </div>

        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#38bdf8" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="tempGradHot" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="hour"
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#64748b", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              domain={["auto", "auto"]}
              tickFormatter={(v) => `${v}°C`}
              width={60}
            />
            <Tooltip content={<TempTooltip threshold={tempThreshold} />} />

            {/* SLA Threshold Reference Line */}
            <ReferenceLine
              y={tempThreshold}
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeDasharray="6 3"
              label={{
                value: `SLA: ${tempThreshold}°C`,
                fill: "#ef4444",
                fontSize: 11,
                position: "insideTopRight",
              }}
            />

            <Area
              type="monotone"
              dataKey="temp_c"
              stroke="#38bdf8"
              strokeWidth={2.5}
              fill="url(#tempGrad)"
              dot={false}
              activeDot={{ r: 5, fill: "#38bdf8", strokeWidth: 0 }}
              name="Temperature (°C)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ── Forensic Anomalies ─────────────────────────────────────────── */}
      {telemetryAnomalies.length > 0 && (
        <div className="rounded-2xl bg-slate-800/50 border border-slate-700/60 p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <span>🚨</span> Forensic Anomaly Report
            <span className="ml-auto text-xs text-slate-500 font-normal">
              Generated by E&amp;I Engine
            </span>
          </h3>
          <div className="space-y-3">
            {telemetryAnomalies.map((a, i) => (
              <AnomalyCard key={i} anomaly={a} />
            ))}
          </div>
        </div>
      )}

      {telemetryAnomalies.length === 0 && (
        <div className="rounded-2xl border border-emerald-500/25 bg-emerald-500/8 p-5 flex items-center gap-3">
          <span className="text-2xl">✅</span>
          <div>
            <p className="text-emerald-300 font-semibold text-sm">No Telemetry Anomalies</p>
            <p className="text-slate-500 text-xs mt-0.5">
              Weight and temperature readings are within normal parameters for this shipment.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default TelemetryDashboard;
