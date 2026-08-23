import React, { useState, useEffect } from 'react';

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters state
  const [filterType, setFilterType] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('date'); // date or amount
  const [sortOrder, setSortOrder] = useState('desc'); // asc or desc

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTx, setEditingTx] = useState(null);

  // New transaction form state
  const [amount, setAmount] = useState('');
  const [txType, setTxType] = useState('Expense');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [paymentMethod, setPaymentMethod] = useState('Other');
  const [aiSuggestion, setAiSuggestion] = useState(null);

  const token = localStorage.getItem('access_token');
  const API_BASE = 'http://127.0.0.1:8000/api';

  useEffect(() => {
    fetchTransactions();
    fetchCategories();
  }, [filterType, filterCategory, startDate, endDate]);

  const fetchTransactions = async () => {
    try {
      let query = `?`;
      if (filterType) query += `transaction_type=${filterType}&`;
      if (filterCategory) query += `category_id=${filterCategory}&`;
      if (startDate) query += `start_date=${startDate}&`;
      if (endDate) query += `end_date=${endDate}&`;

      const res = await fetch(`${API_BASE}/transactions${query}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch transactions');
      const data = await res.json();
      setTransactions(data);
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
        setCategories(data);
      }
    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  };

  // Predict Category from Description using ML route
  const handleDescriptionBlur = async () => {
    if (!description || description.trim().length < 3) return;
    try {
      const res = await fetch(`${API_BASE}/ml/predict-category`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ description, transaction_type: txType })
      });
      if (res.ok) {
        const data = await res.json();
        setAiSuggestion(data);
      }
    } catch (err) {
      console.error('Error predicting category:', err);
    }
  };

  const applyAiSuggestion = () => {
    if (aiSuggestion) {
      setCategoryId(aiSuggestion.category_id);
      setAiSuggestion(null);
    }
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/transactions`, {
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
          date,
          payment_method: paymentMethod
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to add transaction');
      }

      setShowAddModal(false);
      resetForm();
      fetchTransactions();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/transactions/${editingTx.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          amount: parseFloat(amount),
          transaction_type: txType,
          category_id: parseInt(categoryId),
          description,
          date,
          payment_method: paymentMethod
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to update transaction');
      }

      setShowEditModal(false);
      setEditingTx(null);
      resetForm();
      fetchTransactions();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) return;
    try {
      const res = await fetch(`${API_BASE}/transactions/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete transaction');
      fetchTransactions();
    } catch (err) {
      alert(err.message);
    }
  };

  const resetForm = () => {
    setAmount('');
    setTxType('Expense');
    setCategoryId('');
    setDescription('');
    setDate(new Date().toISOString().split('T')[0]);
    setPaymentMethod('Other');
    setAiSuggestion(null);
  };

  const openEditModal = (tx) => {
    setEditingTx(tx);
    setAmount(tx.amount.toString());
    setTxType(tx.transaction_type);
    setCategoryId(tx.category_id || '');
    setDescription(tx.description || '');
    setDate(tx.date);
    setPaymentMethod(tx.payment_method);
    setShowEditModal(true);
  };

  // Client-side text search filter and sorting
  const filteredList = transactions
    .filter(tx => {
      const desc = (tx.description || '').toLowerCase();
      const cat = (tx.category || '').toLowerCase();
      const query = search.toLowerCase();
      return desc.includes(query) || cat.includes(query);
    })
    .sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'date') {
        comparison = new Date(a.date) - new Date(b.date);
      } else {
        comparison = a.amount - b.amount;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#1e293b' }}>Transaction History</h1>
          <p style={{ color: '#64748b', fontSize: '0.95rem' }}>View, search, and manage your income ledger and expense logs.</p>
        </div>
        <button className="btn btn-primary" onClick={() => { resetForm(); setShowAddModal(true); }}>
          Add Transaction
        </button>
      </div>

      {/* Filters Box */}
      <div className="card" style={{ marginBottom: '24px', padding: '16px' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '12px'
        }}>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Search keyword</label>
            <input
              type="text"
              className="form-control"
              placeholder="Search description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Type</label>
            <select className="form-control" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="">All Types</option>
              <option value="Income">Income</option>
              <option value="Expense">Expense</option>
            </select>
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Category</label>
            <select className="form-control" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
              <option value="">All Categories</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>[{c.type[0]}] {c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Start date</label>
            <input
              type="date"
              className="form-control"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>End date</label>
            <input
              type="date"
              className="form-control"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Sort By</label>
            <select className="form-control" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="date">Date</option>
              <option value="amount">Amount</option>
            </select>
          </div>
          <div>
            <label className="form-label" style={{ fontSize: '0.8rem' }}>Order</label>
            <select className="form-control" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Ledger Table */}
      {filteredList.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          No transactions found. Add a transaction or adjust your filters.
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Category</th>
                <th>Description</th>
                <th>Method</th>
                <th style={{ textAlign: 'right' }}>Amount</th>
                <th style={{ width: '120px', textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredList.map((tx) => {
                const d = new Date(tx.date);
                const formattedDate = d.toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' });
                return (
                  <tr key={tx.id}>
                    <td>{formattedDate}</td>
                    <td>
                      <span className={`badge ${tx.transaction_type === 'Income' ? 'badge-income' : 'badge-expense'}`}>
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td>{tx.category || 'Other'}</td>
                    <td>{tx.description}</td>
                    <td>{tx.payment_method}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: tx.transaction_type === 'Income' ? 'var(--success)' : 'var(--text-main)' }}>
                      {tx.transaction_type === 'Income' ? '+' : '-'}${tx.amount.toFixed(2)}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <button className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: '0.8rem' }} onClick={() => openEditModal(tx)}>
                          Edit
                        </button>
                        <button className="btn btn-danger" style={{ padding: '6px 10px', fontSize: '0.8rem' }} onClick={() => handleDelete(tx.id)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Transaction Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">Add Transaction</h3>
            <form onSubmit={handleAddSubmit}>
              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. Dinner with clients, Salary..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  onBlur={handleDescriptionBlur}
                  required
                />
              </div>

              {aiSuggestion && (
                <div style={{
                  backgroundColor: 'var(--primary-light)',
                  border: '1px dashed var(--primary)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  marginBottom: '16px',
                  fontSize: '0.85rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>💡 AI Category Hint: <strong>{aiSuggestion.suggested_category}</strong></span>
                  <button type="button" className="btn btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={applyAiSuggestion}>
                    Apply
                  </button>
                </div>
              )}

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
                    {categories.filter(c => c.type === txType).map(c => (
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
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Payment Method</label>
                <select className="form-control" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                  <option value="Other">Other</option>
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                  <option value="UPI">UPI</option>
                </select>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Save Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Transaction Modal */}
      {showEditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 className="modal-header">Edit Transaction</h3>
            <form onSubmit={handleEditSubmit}>
              <div className="form-group">
                <label className="form-label">Description</label>
                <input
                  type="text"
                  className="form-control"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  onBlur={handleDescriptionBlur}
                  required
                />
              </div>

              {aiSuggestion && (
                <div style={{
                  backgroundColor: 'var(--primary-light)',
                  border: '1px dashed var(--primary)',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  marginBottom: '16px',
                  fontSize: '0.85rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>💡 AI Category Hint: <strong>{aiSuggestion.suggested_category}</strong></span>
                  <button type="button" className="btn btn-primary" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={applyAiSuggestion}>
                    Apply
                  </button>
                </div>
              )}

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
                    {categories.filter(c => c.type === txType).map(c => (
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
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Payment Method</label>
                <select className="form-control" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                  <option value="Other">Other</option>
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                  <option value="UPI">UPI</option>
                </select>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowEditModal(false); setEditingTx(null); }}>Cancel</button>
                <button type="submit" className="btn btn-primary">Update Transaction</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
