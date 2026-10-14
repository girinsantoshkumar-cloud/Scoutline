// Session helpers. The bearer token is kept in localStorage so a page refresh
// keeps the analyst signed in; it is re-validated against /api/auth/me on load.
export type User = { id: string; name: string; email: string; created_at: string }

const TOKEN_KEY = 'scoutline.token'
const USER_KEY = 'scoutline.user'

export function getToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}

export function getUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch { return null }
}

export function setSession(token: string, user: User): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  } catch { /* storage unavailable; session stays in memory only */ }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  } catch { /* ignore */ }
}
