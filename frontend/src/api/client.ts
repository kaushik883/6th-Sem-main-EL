import axios from 'axios';
import type {
  Company,
  Charge,
  ChargeAlias,
  QuoteHeader,
  QuoteDetail,
  QuoteSubmitPayload,
  InvoiceHeader,
  InvoiceDetail,
  AnomalyRead,
  TrackingShipment,
  TrackingEvent,
  Airport,
  Currency,
  UserProfile,
} from './types';

// ─── API Client Configuration ────────────────────────────────────────────────

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8001';

// Axios instance with auth interceptor
const apiClient = axios.create({
  baseURL: API_BASE,
});

// Add JWT token to all requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── AUTH / PROFILE ──────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<{ token: string; user: UserProfile }> {
  const res = await apiClient.post('/api/v1/auth/login', { email, password });
  const { token, user } = res.data;
  localStorage.setItem('auth_token', token);
  return { token, user };
}

export async function logout(): Promise<void> {
  localStorage.removeItem('auth_token');
  await apiClient.post('/api/v1/auth/logout').catch(() => {
    // Ignore errors on logout
  });
}

export async function getMe(): Promise<UserProfile | null> {
  try {
    const res = await apiClient.get('/api/v1/auth/me');
    return res.data;
  } catch (error) {
    return null;
  }
}

// ─── COMPANIES ───────────────────────────────────────────────────────────────

export async function getCompanies(): Promise<Company[]> {
  const res = await apiClient.get('/api/v1/companies');
  return res.data;
}

export async function createCompany(
  payload: Omit<Company, 'id' | 'is_active'> & {
    admin_email: string;
    admin_name: string;
    admin_password: string;
  },
): Promise<Company> {
  const res = await apiClient.post('/api/v1/companies', payload);
  return res.data;
}

export async function updateCompanyStatus(id: number, is_active: boolean): Promise<Company> {
  const res = await apiClient.patch(`/api/v1/companies/${id}/status`, { is_active });
  return res.data;
}

// ─── MASTER DATA ─────────────────────────────────────────────────────────────

export async function getAirports(): Promise<Airport[]> {
  const res = await apiClient.get('/api/v1/masters/airports');
  return res.data;
}

export async function getCurrencies(): Promise<Currency[]> {
  const res = await apiClient.get('/api/v1/masters/currencies');
  return res.data;
}

// ─── CHARGE MASTER ───────────────────────────────────────────────────────────

export async function getCharges(): Promise<Charge[]> {
  const res = await apiClient.get('/api/v1/charges');
  return res.data;
}

export async function createCharge(payload: { name: string; short_name: string }): Promise<Charge> {
  const res = await apiClient.post('/api/v1/charges', payload);
  return res.data;
}

export async function updateCharge(id: number, payload: Partial<Charge>): Promise<Charge> {
  const res = await apiClient.patch(`/api/v1/charges/${id}`, payload);
  return res.data;
}

export async function addAlias(chargeId: number, alias: string): Promise<ChargeAlias> {
  const res = await apiClient.post(`/api/v1/charges/${chargeId}/aliases`, { alias });
  return res.data;
}

export async function deleteAlias(_chargeId: number, aliasId: number): Promise<void> {
  await apiClient.delete(`/api/v1/charges/aliases/${aliasId}`);
}

// ─── QUOTES ──────────────────────────────────────────────────────────────────

export async function getQuotes(): Promise<QuoteHeader[]> {
  const res = await apiClient.get('/api/v1/quotes');
  return res.data;
}

export async function getQuote(id: number): Promise<QuoteDetail> {
  const res = await apiClient.get(`/api/v1/quotes/${id}`);
  return res.data;
}

export async function submitQuote(payload: QuoteSubmitPayload): Promise<QuoteDetail> {
  const res = await apiClient.post('/api/v1/quotes', payload);
  return res.data;
}

export async function updateQuoteStatus(
  id: number,
  status: 'ACCEPTED' | 'REJECTED',
  rejection_note?: string,
): Promise<QuoteDetail> {
  const res = await apiClient.patch(`/api/v1/quotes/${id}/status`, { status, rejection_note });
  return res.data;
}

export async function correctQuoteChargeMapping(chargeId: number, mapped_charge_id: number): Promise<void> {
  await apiClient.patch(`/api/v1/quotes/charges/${chargeId}/mapping`, { mapped_charge_id });
}

// ─── INVOICES ────────────────────────────────────────────────────────────────

export async function getInvoices(quote_id?: number): Promise<InvoiceHeader[]> {
  const params = quote_id ? { quote_id } : {};
  const res = await apiClient.get('/api/v1/invoices', { params });
  return res.data;
}

export async function getInvoice(id: number): Promise<InvoiceDetail> {
  const res = await apiClient.get(`/api/v1/invoices/${id}`);
  return res.data;
}

export async function uploadInvoice(tracking_number: string, file: File): Promise<InvoiceDetail> {
  const formData = new FormData();
  formData.append('tracking_number', tracking_number);
  formData.append('file', file);
  
  const res = await apiClient.post('/api/v1/invoices/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function analyzeInvoice(id: number): Promise<AnomalyRead[]> {
  const res = await apiClient.post(`/api/v1/invoices/${id}/analyze`);
  return res.data;
}

export async function getAnomalies(id: number): Promise<AnomalyRead[]> {
  const res = await apiClient.get(`/api/v1/invoices/${id}/anomalies`);
  return res.data;
}

export async function correctInvoiceChargeMapping(chargeId: number, mapped_charge_id: number): Promise<void> {
  await apiClient.patch(`/api/v1/invoices/charges/${chargeId}/mapping`, { mapped_charge_id });
}

// ─── TRACKING ────────────────────────────────────────────────────────────────

export async function getTracking(): Promise<TrackingShipment[]> {
  const res = await apiClient.get('/api/v1/tracking');
  return res.data;
}

export async function getTrackingEvents(quoteId: number): Promise<TrackingEvent[]> {
  const res = await apiClient.get(`/api/v1/tracking/${quoteId}/events`);
  return res.data;
}

// ─── COPILOT ─────────────────────────────────────────────────────────────────

export async function copilotQuery(question: string): Promise<{ answer: string }> {
  const res = await apiClient.post('/api/v1/copilot/query', { question });
  return res.data;
}

// ─── DASHBOARD STATS ─────────────────────────────────────────────────────────

export async function getDashboardStats() {
  const res = await apiClient.get('/api/v1/dashboard/stats');
  return res.data;
}
