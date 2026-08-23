import React, { useEffect, useState } from 'react';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const token = localStorage.getItem('access_token');
  const API_BASE = 'http://127.0.0.1:8000/api';

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{ padding: '24px', textAlign: 'center' }}>Loading dashboard metrics...</div>;
  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!data) return <div style={{ padding: '24px' }}>No financial ledger records found.</div>;

  const { analytics, ml_insights, budgets, goals, recent_transactions } = data;
  const m = analytics.metrics || {};
  const hasData = analytics.has_data;

  // Find critical warnings from budgets
  const budgetAlerts = budgets.filter(b => b.percent_used >= 90);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Financial Summary</h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Welcome back, {data.user?.username}. Here is your financial outline.</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchDashboardData}>Refresh</button>
      </div>

      {/* Threshold Alerts */}
      {budgetAlerts.map((alert, idx) => (
        <div key={idx} className="alert alert-danger">
          <strong>Budget Alert:</strong> You have spent {alert.percent_used.toFixed(1)}% of your monthly '{alert.category_name}' budget (${alert.total_spent.toFixed(2)} of ${alert.budget_amount.toFixed(2)}).
        </div>
      ))}

      {/* Anomalies alert banner */}
      {ml_insights?.detected_anomalies?.length > 0 && (
        <div className="alert alert-warning" style={{ display: 'block' }}>
          <strong>⚠️ AI Outlier Detected:</strong> Unusual transaction amounts flagged by standard deviation bounds:
          <ul style={{ marginLeft: '20px', marginTop: '6px', fontSize: '0.85rem' }}>
            {ml_insights.detected_anomalies.map((anom, idx) => (
              <li key={idx}>
                {anom.date} - ${anom.amount.toFixed(2)} spent on "{anom.description}" in Category: <strong>{anom.category}</strong> (Avg: ${anom.category_average.toFixed(2)})
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Stats Cards Row */}
      <div className="grid-cols-4">
        <div className="card">
          <span className="stat-label">Total Income</span>
          <div className="stat-value income">${(m.total_income || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="card">
          <span className="stat-label">Total Expenses</span>
          <div className="stat-value expense">${(m.total_expense || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="card">
          <span className="stat-label">Net Savings</span>
          <div className="stat-value" style={{ color: (m.net_savings || 0) >= 0 ? 'var(--success)' : 'var(--danger)' }}>
            ${(m.net_savings || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="card">
          <span className="stat-label">AI Forecast (Next Mo)</span>
          <div className="stat-value" style={{ color: '#6366f1' }}>
            ${(ml_insights?.forecasted_next_month_expenses || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>

      <div className="grid-cols-2">
        {/* Expenses by Category (Horizontal progress chart) */}
        <div className="card">
          <h3 className="card-title">Expense Category Breakdown</h3>
          {!hasData || Object.keys(m.category_percentage || {}).length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No expenses categorized yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {Object.entries(m.category_percentage).map(([catName, pct]) => (
                <div key={catName}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 500 }}>{catName}</span>
                    <span style={{ color: 'var(--text-muted)' }}>{pct.toFixed(1)}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', backgroundColor: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', backgroundColor: 'var(--primary)', borderRadius: '4px' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Savings Goals Status */}
        <div className="card">
          <h3 className="card-title">Savings Goals Progress</h3>
          {goals.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No active goals configured.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {goals.map((g) => (
                <div key={g.goal_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '4px', fontWeight: 500 }}>
                    <span>{g.name}</span>
                    <span>{g.progress_pct.toFixed(1)}%</span>
                  </div>
                  <div style={{ width: '100%', height: '10px', backgroundColor: '#e2e8f0', borderRadius: '5px', overflow: 'hidden', marginBottom: '6px' }}>
                    <div style={{ width: `${Math.min(100, g.progress_pct)}%`, height: '100%', backgroundColor: 'var(--success)', borderRadius: '5px' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>Saved: ${g.current_savings.toLocaleString()} of ${g.target_amount.toLocaleString()}</span>
                    {g.remaining > 0 ? (
                      <span>Need: ${g.required_monthly_savings.toFixed(2)}/mo</span>
                    ) : (
                      <span style={{ color: 'var(--success)', fontWeight: 600 }}>Goal Achieved!</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="grid-cols-2">
        {/* Recent Ledger Entries */}
        <div className="card">
          <h3 className="card-title">Recent Transactions</h3>
          {recent_transactions.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No transactions recorded.</p>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Category</th>
                    <th style={{ textAlign: 'right' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {recent_transactions.map((tx) => {
                    const dateObj = new Date(tx.date);
                    const formattedDate = dateObj.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
                    return (
                      <tr key={tx.id}>
                        <td>{formattedDate}</td>
                        <td>
                          <span className={`badge ${tx.transaction_type === 'Income' ? 'badge-income' : 'badge-expense'}`}>
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td>{tx.category || 'Other'}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600, color: tx.transaction_type === 'Income' ? 'var(--success)' : 'var(--text-main)' }}>
                          {tx.transaction_type === 'Income' ? '+' : '-'}${tx.amount.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Personalized Recommendations */}
        <div className="card">
          <h3 className="card-title">💡 Personal Savings Advice</h3>
          {ml_insights?.recommendations?.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No advice cards compiled yet.</p>
          ) : (
            <div style={{ display: 'flex', flexParagraph: 'column', gap: '12px', flexDirection: 'column' }}>
              {ml_insights.recommendations.map((rec, idx) => (
                <div key={idx} style={{
                  padding: '14px',
                  backgroundColor: 'var(--primary-light)',
                  borderLeft: '4px solid var(--primary)',
                  borderRadius: '0 8px 8px 0',
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: '#1e40af'
                }}>
                  {rec}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
