const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// Football API (match-winner flow)

export async function fetchLeaguesSummary() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/leagues/summary`)
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error fetching leagues:', error)
    throw error
  }
}

export async function fetchTeams(leagueID) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/teams/${leagueID}`)
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error fetching teams:', error)
    throw error
  }
}

export async function predictByTeams(payload) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/game/predict-by-teams`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' }, 
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error predicting match:', error)
    throw error
  }
}



