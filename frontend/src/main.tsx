import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import Login from './Login'
import { getToken, getUser, clearSession, type User } from './auth'
import './styles.css'

function Root() {
  const [user, setUser] = React.useState<User | null>(() => {
    const token = getToken()
    const stored = getUser()
    return token && stored ? stored : null
  })

  const handleAuthenticated = (next: User) => setUser(next)

  const handleSignOut = () => {
    const token = getToken()
    clearSession()
    setUser(null)
    if (token) {
      fetch('/api/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } }).catch(() => {})
    }
  }

  return user
    ? <React.StrictMode><App user={user} onSignOut={handleSignOut} /></React.StrictMode>
    : <React.StrictMode><Login onAuthenticated={handleAuthenticated} /></React.StrictMode>
}

ReactDOM.createRoot(document.getElementById('root')!).render(<Root />)

