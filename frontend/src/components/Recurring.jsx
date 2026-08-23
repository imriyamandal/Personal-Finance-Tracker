import React, { useState, useEffect } from 'react';

export default function Recurring() {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form states
  const [amount, setAmount] = useState('');
  const [txType, setTxType] = useState('Expense');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [frequency, setFrequency] = useState('monthly');
  const [startDate, setStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState('');

  const token = localStorage.getItem('access_token');
  const API_BASE = 'https://personal-finance-api-ce7h.onrender.com/api';

  useEffect(() => {
    fetchTemplates();
    fetchCategories();
  }, [txType]);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE}/recurring`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch scheduled transactions');
      const data = await res.json();
      setTemplates(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/categories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.filter(c => c.type === txType));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!amount || !categoryId || !startDate) return;

    try {
      const res = await fetch(`${API_BASE}/recurring`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: parseFloat(amount),
          transaction_type: txType,
          category_id: parseInt(categoryId),
          description,
          frequency,
          start_date: startDate,
          end_date: endDate || null
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to schedule transaction');
      }

      setAmount('');
      setCategoryId('');
      setDescription('');
      setFrequency('monthly');
      setStartDate(new Date().toISOString().split('T')[0]);
      setEndDate('');
      fetchTemplates();
      alert('Scheduled transaction template created successfully!');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this recurring schedule?')) return;
    try {
      const res = await fetch(`${API_BASE}/recurring/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete scheduled template');
      fetchTemplates();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Recurring Transactions</h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Schedule transactions (like salary, rent, subscriptions) to automatically log over intervals.</p>
      </div>

      <div className="grid-cols-2" style={{ alignItems: 'start' }}>
        {/* Create Schedule Form */}
        <div className="card">
          <h3 className="card-title">Schedule Transaction Template</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Type</label>
                <select className="form-control" value={txType} onChange={(e) => setTxType(e.target.value)}>
                  <option value="Expense">Expense</option>
                  <option value="Income">Income</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Category</label>
                <select className="form-control" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
                  <option value="">Select category</option>
                  {categories.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  placeholder="0.00"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Frequency</label>
                <select className="form-control" value={frequency} onChange={(e) => setFrequency(e.target.value)}>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Description</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Netflix, Rent payment, Salary..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">End Date (Optional)</label>
                <input
                  type="date"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
              Save Schedule Template
            </button>
          </form>
        </div>

        {/* Templates list */}
        <div className="card">
          <h3 className="card-title">Scheduled Pipelines</h3>
          {error && <div className="alert alert-danger">{error}</div>}
          {templates.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No recurring schedules active.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {templates.map((t) => (
                <div key={t.id} style={{
                  padding: '14px',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{t.description || 'Unnamed Schedule'}</span>
                      <span className={`badge ${t.transaction_type === 'Income' ? 'badge-income' : 'badge-expense'}`} style={{ fontSize: '0.65rem' }}>
                        {t.transaction_type}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Category: <strong>{t.category || 'Other'}</strong> | Freq: <strong>{t.frequency}</strong><br />
                      Next run: <strong>{new Date(t.next_occurrence).toLocaleDateString()}</strong>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 700, fontSize: '1.1rem', color: t.transaction_type === 'Income' ? 'var(--success)' : 'var(--text-main)', marginBottom: '6px' }}>
                      ${t.amount.toFixed(2)}
                    </div>
                    <button className="btn btn-danger" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => handleDelete(t.id)}>
                      Cancel
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
