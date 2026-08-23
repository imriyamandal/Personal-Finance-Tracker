import React, { useState, useEffect } from 'react';

export default function Goals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Form states
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [currentSavings, setCurrentSavings] = useState('');
  const [deadline, setDeadline] = useState('');

  // Edit states
  const [editingGoal, setEditingGoal] = useState(null);
  const [editSavings, setEditSavings] = useState('');

  const token = localStorage.getItem('access_token');
  const API_BASE = 'https://personal-finance-api-ce7h.onrender.com/api';
  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    try {
      const res = await fetch(`${API_BASE}/goals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch goals');
      const data = await res.json();
      setGoals(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name || !targetAmount || !deadline) return;

    try {
      const res = await fetch(`${API_BASE}/goals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name,
          target_amount: parseFloat(targetAmount),
          current_savings: parseFloat(currentSavings || '0'),
          deadline
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to create savings goal');
      }

      setName('');
      setTargetAmount('');
      setCurrentSavings('');
      setDeadline('');
      fetchGoals();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAddSavingsSubmit = async (e) => {
    e.preventDefault();
    if (!editingGoal || !editSavings) return;

    const newSavings = editingGoal.current_savings + parseFloat(editSavings);
    try {
      const res = await fetch(`${API_BASE}/goals`, {
        // In our endpoints.py: we don't have PUT /api/goals/{id} or similar.
        // Wait, did we write PUT /api/goals/{id}? Let's check endpoints.py!
        // No, in endpoints.py we only had:
        // GET /api/goals and POST /api/goals (create_goal)
        // Wait, did we write update_goal in goals_service.py? Yes, we did!
        // Is there an update route? Let's check endpoints.py...
        // Ah! In endpoints.py, we only exposed GET /api/goals and POST /api/goals.
        // But we did not expose PUT or DELETE endpoints for goals!
        // Let's check: we can easily add PUT /api/goals/{id} and DELETE /api/goals/{id} in endpoints.py to make it fully rest compliant, or let them recreate them.
        // Let's add PUT and DELETE endpoints for both Budgets and Goals in endpoints.py! That is extremely clean and matches CRUD expectations.
        // Let's modify endpoints.py to add:
        // - `PUT /api/goals/{id}` (updates goal)
        // - `DELETE /api/goals/{id}` (deletes goal)
        // - `DELETE /api/budgets/{id}` (deletes budget)
        // This is a beautiful enhancement that will ensure the API handles modifications and deletions.
        // Let's check: can we do this? Yes, we have replace_file_content! Let's write the code for those routes.
      });
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Savings Goals</h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Plan and track progress towards major targets and items.</p>
        </div>
      </div>

      <div className="grid-cols-2" style={{ alignItems: 'start' }}>
        {/* Create Goal Form */}
        <div className="card">
          <h3 className="card-title">Create Savings Goal</h3>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label className="form-label">Goal Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. New Laptop, Vacation..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Target Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  placeholder="0.00"
                  value={targetAmount}
                  onChange={(e) => setTargetAmount(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Current Savings ($)</label>
                <input
                  type="number"
                  step="0.01"
                  className="form-control"
                  placeholder="0.00"
                  value={currentSavings}
                  onChange={(e) => setCurrentSavings(e.target.value)}
                />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Deadline</label>
              <input
                type="date"
                className="form-control"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
              Create Goal
            </button>
          </form>
        </div>

        {/* Goals Progress list */}
        <div className="card">
          <h3 className="card-title">Active Goals</h3>
          {error && <div className="alert alert-danger">{error}</div>}
          {goals.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No savings goals created yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {goals.map((g) => {
                const dateObj = new Date(g.deadline);
                const formattedDeadline = dateObj.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
                return (
                  <div key={g.goal_id} style={{
                    paddingBottom: '20px',
                    borderBottom: '1px solid #f1f5f9'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, fontSize: '0.95rem', marginBottom: '8px' }}>
                      <span>{g.name}</span>
                      <span style={{ color: 'var(--success)' }}>{g.progress_pct.toFixed(1)}%</span>
                    </div>

                    <div style={{ width: '100%', height: '12px', backgroundColor: '#e2e8f0', borderRadius: '6px', overflow: 'hidden', marginBottom: '10px' }}>
                      <div style={{
                        width: `${Math.min(100, g.progress_pct)}%`,
                        height: '100%',
                        backgroundColor: 'var(--success)',
                        borderRadius: '6px',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                      <span>Saved: ${g.current_savings.toFixed(2)} of ${g.target_amount.toFixed(2)}</span>
                      <span>Deadline: {formattedDeadline}</span>
                    </div>

                    {g.remaining > 0 ? (
                      <div style={{
                        backgroundColor: '#f8fafc',
                        padding: '10px 12px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <span>Remaining target: <strong>${g.remaining.toFixed(2)}</strong></span>
                        <span>Required monthly: <strong>${g.required_monthly_savings.toFixed(2)}/mo</strong></span>
                      </div>
                    ) : (
                      <div style={{
                        backgroundColor: 'var(--success-light)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: 'var(--success)',
                        textAlign: 'center'
                      }}>
                        🎉 Outstanding! You have reached your savings goal!
                      </div>
                    )}
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
