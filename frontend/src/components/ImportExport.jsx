import React, { useState } from 'react';

export default function ImportExport() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const token = localStorage.getItem('access_token');
  const API_BASE = 'https://personal-finance-api-ce7h.onrender.com/api';

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError('');
  };

  const handleImport = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Import failed');
      }
      setResult(data);
      setFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Direct download links
  const downloadUrl = (type) => {
    // Generate auth token as query parameter or use browser direct download
    // Since browser direct link needs headers, we can fetch it, convert it to a blob, and download it!
    // This is the cleanest, most reliable way to download files with JWT headers!
    fetch(`${API_BASE}/export/${type}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Download failed');
      return res.blob();
    })
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transactions_export.${type === 'excel' ? 'xlsx' : type}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    })
    .catch(err => alert(err.message));
  };

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Import / Export Data</h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Upload transactional sheets, or download files to Excel, CSV, or PDF reports.</p>
      </div>

      <div className="grid-cols-2">
        {/* Import Box */}
        <div className="card">
          <h3 className="card-title">Import Transactions</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
            Supported formats: <strong>CSV (.csv)</strong> and <strong>Excel (.xlsx)</strong>.<br />
            Required headers: <code>Date</code>, <code>Amount</code>, <code>Transaction Type</code> (or category type), and <code>Category</code>.
          </p>

          {error && <div className="alert alert-danger">{error}</div>}
          {result && (
            <div className="alert alert-warning" style={{ backgroundColor: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0', display: 'block' }}>
              <strong>Import Finished Successfully!</strong>
              <ul style={{ marginLeft: '20px', marginTop: '6px', fontSize: '0.85rem' }}>
                <li>Imported transactions: {result.imported}</li>
                <li>Duplicates skipped: {result.duplicates_skipped}</li>
                <li>Bad/invalid rows skipped: {result.errors_skipped}</li>
              </ul>
            </div>
          )}

          <form onSubmit={handleImport}>
            <div className="form-group" style={{ marginBottom: '20px' }}>
              <input
                type="file"
                className="form-control"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading || !file}>
              {loading ? 'Importing File...' : 'Upload & Process Sheet'}
            </button>
          </form>
        </div>

        {/* Export Box */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 className="card-title">Export Options</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Download complete transactional archives or generate summary executive reports with visual category tables.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '8px' }}>
            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', padding: '12px 16px' }} onClick={() => downloadUrl('csv')}>
              📥 Download Transaction List as CSV (.csv)
            </button>
            
            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', padding: '12px 16px' }} onClick={() => downloadUrl('excel')}>
              📊 Download Spreadsheet as Excel (.xlsx)
            </button>
            
            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', padding: '12px 16px' }} onClick={() => downloadUrl('pdf')}>
              📄 Compile Styled Financial PDF Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
