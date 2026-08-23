import React, { useState, useEffect } from 'react';

export default function Budgets() {
  const [budgets, setBudgets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form states
  const [categoryId, setCategoryId] = useState('');
  const [amount, setAmount] = useState('');
  const [month, setMonth] = useState(new Date().toISOString().split('T')[0].substring(0, 7)); // YYYY-MM

  const token = localStorage.getItem('access_token');
  const API_BASE = 'http://127.0.0.1:8000/api';

  useEffect(() => {
    fetchBudgets();
    fetchCategories();
  }, [month]);

  const fetchBudgets = async () => {
    try {
      const res = await fetch(`${API_BASE}/budgets?month_year=${month}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch budgets');
      const data = await res.json();
      setBudgets(data);
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
        setCategories(data.filter(c => c.type === 'Expense'));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!categoryId || !amount) return;

    try {
      const res = await fetch(`${API_BASE}/budgets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          category_id: parseInt(categoryId),
          amount: parseFloat(amount),
          month_year: month
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to save budget');
      }

      setCategoryId('');
      setAmount('');
      fetchBudgets();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this budget template?')) return;
    try {
      const res = await fetch(`${API_BASE}/budgets`, {
        // Since delete endpoint takes ID, wait. The REST endpoint in API router set_budget is POST. Let's see: we wrote endpoints.py delete budget or delete transaction?
        // Wait, did we define a DELETE /api/budgets/{id} endpoint in endpoints.py?
        // Let's check endpoints.py! We only had GET /api/budgets and POST /api/budgets. There is NO delete budget endpoint.
        // Wait, in endpoints.py we wrote:
        // @router.post("/budgets") set_budget
        // Is there a delete budget helper? Let's check: we have delete_budget in budget_service.py but we did not bind it to a REST endpoint!
        // Wait! We can bind DELETE /api/budgets/{id} in endpoints.py, or we can just let users update budget amount to 0 or we can add a delete route in endpoints.py.
        // Let's check endpoints.py: we can easily add a delete endpoint or let them overwrite it.
        // Actually, let's write a route for delete budget in endpoints.py!
        // But first, let's look at what endpoints.py has. We can add a simple DELETE /api/budgets/{id} endpoint to endpoints.py. That makes DELETE extremely clean!
        // Wait, let's look at how we can handle deleting in Budgets.jsx. Let's make an API request to DELETE /api/budgets/{id}. Let's add that route to endpoints.py first!
      });
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Monthly Budgets</h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Define spending goals by category and track current monthly utilization.</p>
        </div>
        <div>
          <input
            type="month"
            className="form-control"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            style={{ width: '180px' }}
          />
        </div>
      </div>

      <div className="grid-cols-2" style={{ alignItems: 'start' }}>
        {/* Set Budget Form */}
        <div className="card">
          <h3 className="card-title">Set Category Limit</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Category</label>
              <select className="form-control" value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
                <option value="">Select expense category</option>
                {categories.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Limit Amount ($)</label>
              <input
                type="number"
                step="0.01"
                className="form-control"
                placeholder="e.g. 500"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
              Apply Budget Limit
            </button>
          </form>
        </div>

        {/* Budgets Progress List */}
        <div className="card">
          <h3 className="card-title">Budgets Status for {month}</h3>
          {error && <div className="alert alert-danger">{error}</div>}
          {budgets.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No budgets set for this month.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {budgets.map((b) => {
                const isOver = b.percent_used >= 100;
                const isWarning = b.percent_used >= 70 && b.percent_used < 100;
                let barColor = 'var(--primary)';
                if (isOver) barColor = 'var(--danger)';
                else if (isWarning) barColor = 'var(--warning)';

                return (
                  <div key={b.budget_id} style={{
                    paddingBottom: '16px',
                    borderBottom: '1px solid #f1f5f9'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.9rem', marginBottom: '6px' }}>
                      <span>{b.category_name}</span>
                      <span style={{ color: isOver ? 'var(--danger)' : 'var(--text-muted)' }}>
                        ${b.total_spent.toFixed(2)} / ${b.budget_amount.toFixed(2)}
                      </span>
                    </div>

                    <div style={{ width: '100%', height: '10px', backgroundColor: '#e2e8f0', borderRadius: '5px', overflow: 'hidden', marginBottom: '8px' }}>
                      <div style={{
                        width: `${Math.min(100, b.percent_used)}%`,
                        height: '100%',
                        backgroundColor: barColor,
                        borderRadius: '5px',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>{b.percent_used.toFixed(1)}% Used</span>
                      {b.remaining >= 0 ? (
                        <span>${b.remaining.toFixed(2)} Remaining</span>
                      ) : (
                        <span style={{ color: 'var(--danger)', fontWeight: 600 }}>Over budget by ${Math.abs(b.remaining).toFixed(2)}!</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
