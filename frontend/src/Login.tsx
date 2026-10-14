import { useState } from 'react'
import { ArrowUpRight, CircleAlert, ShieldCheck, Sparkles } from 'lucide-react'
import { setSession, type User } from './auth'

type Props = { onAuthenticated: (user: User) => void }

type Mode = 'signin' | 'signup'

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  const text = await response.text()
  if (!response.ok) {
    let message = text
    try { const parsed = JSON.parse(text); message = parsed.detail || text } catch { /* keep raw text */ }
    throw new Error(message)
  }
  return JSON.parse(text) as T
}

export default function Login({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<Mode>('signin')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = mode === 'signup'
        ? await postJson<{ user: User; token: string }>('/api/auth/register', { name, email, password })
        : await postJson<{ user: User; token: string }>('/api/auth/login', { email, password })
      setSession(result.token, result.user)
      onAuthenticated(result.user)
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setLoading(false)
    }
  }

  const switchMode = () => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError('') }

  return (
    <div className="auth-shell">
      <aside className="auth-hero">
        <div className="brand auth-brand"><div className="brand-mark"><Sparkles size={17} /></div><span>scoutline</span></div>
        <div className="hero-kicker"><span className="dot"></span> REAL PUBLIC WEB EVIDENCE</div>
        <h2>Turn a role brief into<br /><em>defensible shortlists.</em></h2>
        <p>Sign in to your recruiting workspace. Scoutline investigates public professional signals across GitHub and the web, then shows exactly what supports each match.</p>
        <div className="auth-hero-note"><ShieldCheck size={16} /><div><strong>Evidence-first</strong><span>Public professional data only</span></div></div>
      </aside>

      <main className="auth-panel">
        <div className="auth-card">
          <span className="eyebrow">{mode === 'signin' ? 'WELCOME BACK' : 'CREATE ACCOUNT'}</span>
          <h1>{mode === 'signin' ? 'Sign in to Scoutline' : 'Start your workspace'}</h1>
          <p className="auth-sub">{mode === 'signin' ? 'Access the research desk and your recent searches.' : 'Create an account to run evidence-first candidate research.'}</p>

          <form onSubmit={submit}>
            {mode === 'signup' && (
              <label>Full name
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Avery Chen" autoComplete="name" required />
              </label>
            )}
            <label>Work email
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email" required />
            </label>
            <label>Password
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" autoComplete={mode === 'signin' ? 'current-password' : 'new-password'} required />
            </label>

            {error && (
              <div className="alert"><CircleAlert size={17} /><span>{error}</span></div>
            )}

            <button className="find-button auth-submit" type="submit" disabled={loading}>
              {loading ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'} <ArrowUpRight size={16} />
            </button>
          </form>

          <button className="auth-switch" onClick={switchMode}>
            {mode === 'signin' ? "Don't have an account? Create one" : 'Already have an account? Sign in'}
          </button>
        </div>
      </main>
    </div>
  )
}
