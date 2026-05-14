import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, ArrowRight, FileText, AlertCircle, X } from 'lucide-react';
import { getInvoices, getQuotes, uploadInvoice } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export function Invoices() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const qc = useQueryClient();
  const isForwarder = user?.role === 'forwarder';
  const isClient = user?.role === 'client';

  const [showUpload, setShowUpload] = useState(false);
  const [trackingNumber, setTrackingNumber] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => getInvoices(),
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadInvoice(trackingNumber, selectedFile!),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['invoices'] });
      setShowUpload(false);
      setTrackingNumber('');
      setSelectedFile(null);
      setUploadError(null);
      navigate(`/app/invoices/${data.id}`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail?.message || err.message;
      setUploadError(msg);
    },
  });

  const handleUpload = () => {
    if (!trackingNumber.trim()) { setUploadError('Enter a tracking number'); return; }
    if (!selectedFile) { setUploadError('Select a PDF file'); return; }
    setUploadError(null);
    uploadMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Invoices</h1>
          <p className="text-slate-400 mt-1 text-sm">
            {isClient ? 'Review and analyse uploaded freight invoices' : 'Upload invoice PDFs using tracking numbers'}
          </p>
        </div>
        {isForwarder && (
          <button
            onClick={() => setShowUpload(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold transition-colors"
          >
            <Upload className="w-4 h-4" /> Upload Invoice
          </button>
        )}
      </div>

      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl">
            <div className="flex items-center justify-between p-5 border-b border-slate-800">
              <h2 className="text-base font-semibold text-slate-100">Upload Invoice</h2>
              <button
                onClick={() => { setShowUpload(false); setSelectedFile(null); setTrackingNumber(''); setUploadError(null); }}
                className="text-slate-500 hover:text-slate-300"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              {uploadError && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-950/60 border border-red-800">
                  <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-300">{uploadError}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Tracking Number</label>
                <input
                  type="text"
                  placeholder="e.g. TRK-INV-123"
                  value={trackingNumber}
                  onChange={(e) => setTrackingNumber(e.target.value)}
                  className="input-field"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Invoice PDF</label>
                <div
                  onClick={() => fileRef.current?.click()}
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    selectedFile
                      ? 'border-sky-700 bg-sky-950/20'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                  />
                  <Upload className={`w-8 h-8 mx-auto mb-2 ${selectedFile ? 'text-sky-400' : 'text-slate-600'}`} />
                  {selectedFile ? (
                    <p className="text-sm text-sky-300 font-medium">{selectedFile.name}</p>
                  ) : (
                    <>
                      <p className="text-sm text-slate-400">Click to select PDF</p>
                      <p className="text-xs text-slate-600 mt-1">Supports digital and scanned PDFs</p>
                    </>
                  )}
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShowUpload(false); setSelectedFile(null); setTrackingNumber(''); setUploadError(null); }}
                  className="flex-1 py-2.5 rounded-lg border border-slate-700 text-slate-300 text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending}
                  className="flex-1 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
                >
                  {uploadMutation.isPending ? 'Uploading…' : 'Upload & Extract'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-lg border border-slate-800 bg-slate-900/40 animate-pulse" />
          ))}
        </div>
      ) : invoices.length === 0 ? (
        <div className="py-24 text-center">
          <FileText className="w-12 h-12 text-slate-700 mx-auto mb-4" />
          <p className="text-slate-400 font-medium">No invoices yet</p>
          {isForwarder && (
            <button
              onClick={() => setShowUpload(true)}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold transition-colors"
            >
              <Upload className="w-4 h-4" /> Upload first invoice
            </button>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60">
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Invoice #</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Quote Ref</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Invoice Date</th>
                <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Uploaded</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr
                  key={inv.id}
                  className="border-b border-slate-800/60 hover:bg-slate-800/30 cursor-pointer transition-colors"
                  onClick={() => navigate(`/app/invoices/${inv.id}`)}
                >
                  <td className="px-5 py-3.5 font-mono text-sky-400 font-medium">{inv.invoice_number}</td>
                  <td className="px-5 py-3.5 font-mono text-slate-400 text-xs">{inv.quote?.quote_ref ?? '—'}</td>
                  <td className="px-5 py-3.5 text-slate-400 text-xs">{inv.invoice_date}</td>
                  <td className="px-5 py-3.5 text-slate-500 text-xs">
                    {new Date(inv.uploaded_at).toLocaleDateString()}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <ArrowRight className="w-4 h-4 text-slate-600 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
