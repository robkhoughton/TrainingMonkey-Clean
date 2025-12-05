import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      style={{
        backgroundColor: '#1e293b',
        color: '#e2e8f0',
        padding: '0.75rem 1.5rem 0.5rem',
        marginTop: 'auto',
        borderTop: '2px solid #0f172a'
      }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '1rem',
        marginBottom: '0.5rem'
      }}>
        {/* Company Info */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.35rem',
            justifyContent: 'center'
          }}>
            <h3 style={{
              color: '#fff',
              fontSize: '0.95rem',
              margin: 0,
              fontWeight: '600',
              fontStyle: 'italic'
            }}>
              Your Training Monkey
            </h3>
            <a href="/faq#patent-technology" style={{
              display: 'inline-block',
              background: 'rgba(255,255,255,0.1)',
              padding: '0.25rem 0.5rem',
              borderRadius: '3px',
              fontSize: '0.7rem',
              fontWeight: '600',
              color: '#cbd5e1',
              textDecoration: 'none',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = '#cbd5e1';
            }}>
              Patent Pending
            </a>
          </div>
          <p style={{
            fontSize: '0.8rem',
            lineHeight: '1.4',
            color: '#cbd5e1',
            margin: 0
          }}>
            Built for trail runners by trail runners.<br />Train smarter, prevent injuries, optimize performance.
          </p>
        </div>

        {/* Legal */}
        <div style={{ textAlign: 'center' }}>
          <h3 style={{
            color: '#fff',
            fontSize: '0.95rem',
            margin: 0,
            marginBottom: '0.35rem',
            fontWeight: '600'
          }}>
            Legal
          </h3>
          <ul style={{
            listStyle: 'none',
            padding: 0,
            margin: 0
          }}>
            <li style={{ marginBottom: '0.1rem' }}>
              <a href="/legal/privacy" target="_blank" rel="noopener noreferrer" style={{
                color: '#cbd5e1',
                textDecoration: 'none',
                fontSize: '0.8rem',
                transition: 'color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
              onMouseOut={(e) => e.currentTarget.style.color = '#cbd5e1'}>
                Privacy Policy
              </a>
            </li>
            <li style={{ marginBottom: '0.1rem' }}>
              <a href="/legal/terms" target="_blank" rel="noopener noreferrer" style={{
                color: '#cbd5e1',
                textDecoration: 'none',
                fontSize: '0.8rem',
                transition: 'color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
              onMouseOut={(e) => e.currentTarget.style.color = '#cbd5e1'}>
                Terms &amp; Conditions
              </a>
            </li>
            <li style={{ marginBottom: '0.1rem' }}>
              <a href="/legal/disclaimer" target="_blank" rel="noopener noreferrer" style={{
                color: '#cbd5e1',
                textDecoration: 'none',
                fontSize: '0.8rem',
                transition: 'color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
              onMouseOut={(e) => e.currentTarget.style.color = '#cbd5e1'}>
                Medical Disclaimer
              </a>
            </li>
          </ul>
        </div>

        {/* Support */}
        <div style={{ textAlign: 'center' }}>
          <h3 style={{
            color: '#fff',
            fontSize: '0.95rem',
            margin: 0,
            marginBottom: '0.35rem',
            fontWeight: '600'
          }}>
            Support
          </h3>
          <a href="mailto:support@yourtrainingmonkey.com" style={{
            color: '#cbd5e1',
            textDecoration: 'none',
            fontSize: '0.8rem',
            transition: 'color 0.2s'
          }}
          onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
          onMouseOut={(e) => e.currentTarget.style.color = '#cbd5e1'}>
            support@yourtrainingmonkey.com
          </a>
        </div>
      </div>

      {/* Copyright */}
      <div style={{
        borderTop: '1px solid #0f172a',
        paddingTop: '0.4rem',
        marginTop: '0.4rem',
        fontSize: '0.75rem',
        color: '#94a3b8',
        textAlign: 'center'
      }}>
        &copy; {currentYear} <span style={{ fontStyle: 'italic' }}>Your Training Monkey</span>, LLC. All rights reserved.
      </div>
    </footer>
  );
};

export default Footer;
