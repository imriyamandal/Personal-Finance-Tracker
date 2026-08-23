import React, { useState, useEffect } from 'react';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import Transactions from './components/Transactions';
import Budgets from './components/Budgets';
import Goals from './components/Goals';
import Recurring from './components/Recurring';
import ImportExport from './components/ImportExport';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [username, setUsername] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('username');
    if (token) {
      setIsAuthenticated(true);
      setUsername(storedUser || 'User');
    }
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setUsername(localStorage.getItem('username') || 'User');
    setActiveTab('dashboard');
  };

  const handleSignOut = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Auth onLoginSuccess={handleLoginSuccess} />;
  }

  // Render correct component based on activeTab
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'transactions':
        return <Transactions />;
      case 'budgets':
        return <Budgets />;
      case 'goals':
        return <Goals />;
      case 'recurring':
        return <Recurring />;
      case 'import-export':
        return <ImportExport />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div>
          <div className="brand-title">Finance Manager</div>
          <nav>
            <ul className="nav-list">
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('dashboard')}
                >
                  <span>📊</span> Dashboard
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'transactions' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('transactions')}
                >
                  <span>💸</span> Transactions
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'budgets' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('budgets')}
                >
                  <span>📈</span> Monthly Budgets
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'goals' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('goals')}
                >
                  <span>🎯</span> Savings Goals
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'recurring' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('recurring')}
                >
                  <span>🔁</span> Recurring Tasks
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'import-export' ? 'active' : ''}`}
                  style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
                  onClick={() => setActiveTab('import-export')}
                >
                  <span>📥</span> Import / Export
                </button>
              </li>
            </ul>
          </nav>
        </div>

        <div className="sidebar-footer">
          <div style={{ padding: '0 12px 12px 12px', fontSize: '0.85rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span>Logged in as:</span>
            <strong style={{ color: '#ffffff' }}>{username}</strong>
          </div>
          <button className="btn btn-danger" style={{ width: '100%', padding: '8px 16px', fontSize: '0.85rem' }} onClick={handleSignOut}>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Panel content */}
      <main className="main-content">
        {renderContent()}
      </main>
    </div>
  );
}
