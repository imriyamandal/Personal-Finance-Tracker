import React, { useState } from 'react';

export default function Auth({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = 'http://127.0.0.1:8000/api';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        // Register API Call
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Registration failed');
        }
        
        // Auto Login after successful registration
        setIsRegister(false);
        setPassword('');
        setError('Registration successful! Please login.');
      } else {
        // Login API Call
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString(),
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Incorrect username or password');
        }

        // Save token and invoke success callback
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('username', username);
        onLoginSuccess();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#f1f5f9',
      padding: '16px'
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <h2 style={{
          textAlign: 'center',
          fontSize: '1.5rem',
          fontWeight: 700,
          marginBottom: '24px',
          color: '#1e293b'
        }}>
          Personal Finance Tracker
        </h2>
        
        <h3 className="card-title" style={{ textAlign: 'center', marginBottom: '20px' }}>
          {isRegister ? 'Create an Account' : 'Sign In'}
        </h3>

        {error && (
          <div className="alert alert-danger" style={{ padding: '8px 12px', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-control"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-control"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }} disabled={loading}>
            {loading ? 'Processing...' : (isRegister ? 'Sign Up' : 'Sign In')}
          </button>
        </form>

        <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.875rem', color: '#64748b' }}>
          {isRegister ? (
            <span>
              Already have an account?{' '}
              <button
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '0.8rem' }}
                onClick={() => { setIsRegister(false); setError(''); }}
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Don't have an account?{' '}
              <button
                className="btn btn-secondary"
                style={{ padding: '2px 8px', fontSize: '0.8rem' }}
                onClick={() => { setIsRegister(true); setError(''); }}
              >
                Register
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
