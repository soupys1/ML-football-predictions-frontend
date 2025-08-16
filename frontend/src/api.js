const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://football-predictor-backend-77ec5580ef7d.herokuapp.com'

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

export async function trainModel() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/game/train-with-teams-players`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error training model:', error)
    throw error
  }
}

export async function getModelStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/model/status`)
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error getting model status:', error)
    throw error
  }
}

export async function uploadData() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/football/data/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`)
    }
    return res.json()
  } catch (error) {
    console.error('Error uploading data:', error)
    throw error
  }
}