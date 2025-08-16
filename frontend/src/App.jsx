import React, { useEffect, useState } from 'react'
import { fetchLeaguesSummary, fetchTeams, predictByTeams, getModelStatus } from './api'

export default function App() {
  const [leagues, setLeagues] = useState([])
  const [selectedLeague, setSelectedLeague] = useState('')
  const [teams, setTeams] = useState([])
  const [homeTeamID, setHomeTeamID] = useState('')
  const [awayTeamID, setAwayTeamID] = useState('')
  const [gameOut, setGameOut] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [animateResults, setAnimateResults] = useState(false)
  const [darkMode, setDarkMode] = useState(true)
  const [apiStatus, setApiStatus] = useState('checking')

  async function loadLeagues() {
    try {
      const data = await fetchLeaguesSummary()
      setLeagues(data.leagues || [])
      setApiStatus('connected')
    } catch (e) {
      console.error('Failed to load leagues:', e)
      setApiStatus('error')
    }
  }

  useEffect(() => {
    loadLeagues()
  }, [])

  async function onLeagueChange(id) {
    setSelectedLeague(id)
    setTeams([])
    setHomeTeamID('')
    setAwayTeamID('')
    setGameOut(null)
    setAnimateResults(false)
    if (!id) return
    try {
      const data = await fetchTeams(id)
      setTeams(data.teams || [])
    } catch (e) { 
      setError(e?.message || 'Failed to load teams') 
    }
  }

  async function onPredictMatch(e) {
    e.preventDefault()
    setError('')
    setGameOut(null)
    setAnimateResults(false)
    
    console.log('DEBUG: Form data:', { selectedLeague, homeTeamID, awayTeamID }) // Debug log
    
    if (!selectedLeague || !homeTeamID || !awayTeamID || homeTeamID === awayTeamID) {
      setError('Select a league and two different teams')
      return
    }
    
    const payload = { 
      leagueID: Number(selectedLeague), 
      homeTeamID: Number(homeTeamID), 
      awayTeamID: Number(awayTeamID) 
    }
    
    console.log('DEBUG: Sending payload:', payload) // Debug log
    
    try {
      setLoading(true)
      const res = await predictByTeams(payload)
      console.log('DEBUG: Received response:', res) // Debug log
      setGameOut(res)
      // Trigger animation after a short delay
      setTimeout(() => setAnimateResults(true), 100)
    } catch (e) {
      console.error('DEBUG: Error:', e) // Debug log
      setError(e?.message || 'Prediction failed')
    }
    setLoading(false)
  }

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }

  return (
    <div className={`min-h-screen font-sans overflow-x-hidden transition-colors duration-300 ${
      darkMode 
        ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white' 
        : 'bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 text-gray-900'
    }`}>
      {/* Animated background particles */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-1/4 left-1/4 w-2 h-2 rounded-full animate-pulse opacity-30 ${
          darkMode ? 'bg-slate-400' : 'bg-gray-400'
        }`}></div>
        <div className={`absolute top-1/3 right-1/3 w-1 h-1 rounded-full animate-bounce opacity-20 ${
          darkMode ? 'bg-slate-300' : 'bg-gray-300'
        }`}></div>
        <div className={`absolute bottom-1/4 left-1/3 w-1.5 h-1.5 rounded-full animate-ping opacity-25 ${
          darkMode ? 'bg-slate-500' : 'bg-gray-500'
        }`}></div>
        <div className={`absolute top-1/2 right-1/4 w-1 h-1 rounded-full animate-pulse opacity-30 ${
          darkMode ? 'bg-slate-400' : 'bg-gray-400'
        }`}></div>
      </div>

      <header className={`relative text-white transition-colors duration-300 ${
        darkMode 
          ? 'bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700' 
          : 'bg-gradient-to-r from-gray-600 via-gray-500 to-gray-600'
      }`}>
        <div className="mx-auto max-w-6xl px-4 py-20">
          <nav className="flex items-center justify-between mb-12">
            <div className="text-3xl font-bold tracking-tight">
              <span className={`bg-clip-text text-transparent ${
                darkMode 
                  ? 'bg-gradient-to-r from-slate-200 to-slate-300' 
                  : 'bg-gradient-to-r from-gray-100 to-gray-200'
              }`}>
                ⚽ Match Predictor
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm">
              <a href="#leagues" className={`transition-all duration-300 hover:scale-110 transform ${
                darkMode ? 'hover:text-slate-200' : 'hover:text-gray-100'
              }`}>Leagues</a>
              <a href="#predict" className={`transition-all duration-300 hover:scale-110 transform ${
                darkMode ? 'hover:text-slate-200' : 'hover:text-gray-100'
              }`}>Predict</a>
              <a href="#about" className={`transition-all duration-300 hover:scale-110 transform ${
                darkMode ? 'hover:text-slate-200' : 'hover:text-gray-100'
              }`}>About</a>
              <button
                onClick={toggleDarkMode}
                className={`p-2 rounded-lg transition-all duration-300 hover:scale-110 ${
                  darkMode 
                    ? 'bg-slate-600 hover:bg-slate-500' 
                    : 'bg-gray-500 hover:bg-gray-400'
                }`}
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
            </div>
          </nav>
          <div className="text-center">
            <h1 className={`text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent ${
              darkMode 
                ? 'bg-gradient-to-r from-slate-100 via-slate-200 to-slate-300' 
                : 'bg-gradient-to-r from-gray-900 via-gray-800 to-gray-700'
            }`}>
              Football Match Predictor
            </h1>
            <p className={`text-xl max-w-3xl mx-auto leading-relaxed ${
              darkMode ? 'text-slate-300' : 'text-gray-200'
            }`}>
              AI-powered predictions for football match outcomes. Select teams, get predictions, and discover top performers with advanced analytics.
            </p>
          </div>
        </div>
      </header>

      {/* API Status Indicator */}
      <div className="relative mx-auto max-w-6xl px-4 py-2">
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
          apiStatus === 'connected' 
            ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
            : apiStatus === 'error'
            ? 'bg-red-500/20 text-red-300 border border-red-500/30'
            : 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            apiStatus === 'connected' ? 'bg-green-400 animate-pulse' 
            : apiStatus === 'error' ? 'bg-red-400' 
            : 'bg-yellow-400 animate-spin'
          }`}></div>
          {apiStatus === 'connected' ? 'API Connected' 
           : apiStatus === 'error' ? 'API Error' 
           : 'Connecting to API...'}
        </div>
      </div>

      <main className="relative mx-auto max-w-6xl px-4 py-12">
        <section id="leagues" className={`backdrop-blur-xl border rounded-3xl shadow-2xl p-8 mb-12 transition-all duration-500 hover:scale-105 ${
          darkMode 
            ? 'bg-white/5 border-white/10 hover:shadow-slate-500/25' 
            : 'bg-white/80 border-gray-200/50 hover:shadow-gray-500/25'
        }`}>
          <div className="mb-6">
            <h2 className={`text-2xl font-semibold mb-3 bg-clip-text text-transparent ${
              darkMode 
                ? 'bg-gradient-to-r from-slate-200 to-slate-300' 
                : 'bg-gradient-to-r from-gray-700 to-gray-800'
            }`}>
              Available Leagues
            </h2>
            <p className={darkMode ? 'text-slate-300' : 'text-gray-600'}>
              Select a league to view available teams
            </p>
          </div>
          {leagues.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {leagues.map((league, i) => (
                <div 
                  key={i} 
                  className={`p-6 rounded-2xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:rotate-1 cursor-pointer group ${
                    darkMode 
                      ? 'border-slate-500/20 bg-gradient-to-br from-slate-500/10 to-slate-600/10 hover:shadow-slate-500/25' 
                      : 'border-gray-300/50 bg-gradient-to-br from-gray-100/50 to-gray-200/50 hover:shadow-gray-500/25'
                  }`}
                  style={{ animationDelay: `${i * 100}ms` }}
                  onClick={() => onLeagueChange(league.leagueID)}
                >
                  <div className={`font-semibold transition-colors duration-300 ${
                    darkMode 
                      ? 'text-slate-200 group-hover:text-slate-100' 
                      : 'text-gray-700 group-hover:text-gray-800'
                  }`}>
                    {league.name || 'Unknown League'}
                  </div>
                  <div className={`text-sm mt-2 opacity-80 ${
                    darkMode ? 'text-slate-400' : 'text-gray-500'
                  }`}>
                    ID {league.leagueID} • {league.numGames} games
                  </div>
                  <div className={`mt-3 w-full rounded-full h-2 ${
                    darkMode ? 'bg-slate-700' : 'bg-gray-300'
                  }`}>
                    <div 
                      className={`h-2 rounded-full transition-all duration-1000 ${
                        darkMode 
                          ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
                          : 'bg-gradient-to-r from-gray-500 to-gray-600'
                      }`}
                      style={{ width: `${Math.min((league.numGames / 1000) * 100, 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={`text-center py-12 ${darkMode ? 'text-slate-300' : 'text-gray-600'}`}>
              <div className="text-4xl mb-4">🏟️</div>
              <div>No leagues available. Make sure your backend is running and data is loaded.</div>
            </div>
          )}
        </section>

        <section id="predict" className="grid lg:grid-cols-2 gap-8">
          <div className={`backdrop-blur-xl border rounded-3xl shadow-2xl p-8 transition-all duration-500 ${
            animateResults ? 'animate-pulse' : ''
          } ${
            darkMode 
              ? 'bg-white/5 border-white/10' 
              : 'bg-white/80 border-gray-200/50'
          }`}>
            <h2 className={`text-2xl font-semibold mb-6 bg-clip-text text-transparent ${
              darkMode 
                ? 'bg-gradient-to-r from-slate-200 to-slate-300' 
                : 'bg-gradient-to-r from-gray-700 to-gray-800'
            }`}>
              Predict Match Winner
            </h2>
            <form onSubmit={onPredictMatch} className="space-y-6">
              <div className="transition-all duration-300">
                <label className={`block text-sm font-medium mb-3 ${
                  darkMode ? 'text-slate-300' : 'text-gray-700'
                }`}>League</label>
                <select 
                  className={`w-full rounded-xl border text-base px-6 py-4 focus:outline-none focus:ring-2 transition-all duration-300 backdrop-blur-sm shadow-lg ${
                    darkMode 
                      ? 'border-slate-500/30 bg-slate-500/10 text-white focus:ring-slate-400 focus:border-slate-400 placeholder-slate-400/50' 
                      : 'border-gray-300/50 bg-white/50 text-gray-900 focus:ring-gray-400 focus:border-gray-400 placeholder-gray-500/50'
                  }`}
                  style={{
                    colorScheme: darkMode ? 'dark' : 'light'
                  }}
                  value={selectedLeague} 
                  onChange={e => onLeagueChange(e.target.value)}
                >
                  <option value="" className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}>
                    Select a league
                  </option>
                  {leagues.map((league) => (
                    <option 
                      key={league.leagueID} 
                      value={league.leagueID}
                      className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}
                    >
                      {league.name || `League ${league.leagueID}`}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div className="transition-all duration-300">
                  <label className={`block text-sm font-medium mb-3 ${
                    darkMode ? 'text-slate-300' : 'text-gray-700'
                  }`}>Home Team</label>
                  <select 
                    className={`w-full rounded-xl border text-base px-6 py-4 focus:outline-none focus:ring-2 transition-all duration-300 backdrop-blur-sm shadow-lg ${
                      darkMode 
                        ? 'border-slate-500/30 bg-slate-500/10 text-white focus:ring-slate-400 focus:border-slate-400 placeholder-slate-400/50' 
                        : 'border-gray-300/50 bg-white/50 text-gray-900 focus:ring-gray-400 focus:border-gray-400 placeholder-gray-500/50'
                    }`}
                    style={{
                      colorScheme: darkMode ? 'dark' : 'light'
                    }}
                    disabled={!teams.length} 
                    value={homeTeamID} 
                    onChange={e => setHomeTeamID(e.target.value)}
                  >
                    <option value="" className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}>
                      Select home team
                    </option>
                    {teams.map(team => (
                      <option 
                        key={team.teamID || team.id} 
                        value={team.teamID || team.id}
                        className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}
                      >
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="transition-all duration-300">
                  <label className={`block text-sm font-medium mb-3 ${
                    darkMode ? 'text-slate-300' : 'text-gray-700'
                  }`}>Away Team</label>
                  <select 
                    className={`w-full rounded-xl border text-base px-6 py-4 focus:outline-none focus:ring-2 transition-all duration-300 backdrop-blur-sm shadow-lg ${
                      darkMode 
                        ? 'border-slate-500/30 bg-slate-500/10 text-white focus:ring-slate-400 focus:border-slate-400 placeholder-slate-400/50' 
                        : 'border-gray-300/50 bg-white/50 text-gray-900 focus:ring-gray-400 focus:border-gray-400 placeholder-gray-500/50'
                    }`}
                    style={{
                      colorScheme: darkMode ? 'dark' : 'light'
                    }}
                    disabled={!teams.length} 
                    value={awayTeamID} 
                    onChange={e => setAwayTeamID(e.target.value)}
                  >
                    <option value="" className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}>
                      Select away team
                    </option>
                    {teams.map(team => (
                      <option 
                        key={team.teamID || team.id} 
                        value={team.teamID || team.id}
                        className={darkMode ? 'bg-slate-800 text-white' : 'bg-white text-gray-900'}
                      >
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  type="submit" 
                  className={`inline-flex items-center justify-center rounded-xl px-8 py-4 font-semibold transition-all duration-300 shadow-lg hover:shadow-2xl transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none group ${
                    darkMode 
                      ? 'bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white' 
                      : 'bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white'
                  }`}
                  disabled={!selectedLeague || !homeTeamID || !awayTeamID || homeTeamID === awayTeamID}
                >
                  <span className="group-hover:animate-bounce">🔮</span>
                  <span className="ml-2">Predict Winner</span>
                </button>
                {loading && (
                  <div className={`flex items-center gap-2 ${
                    darkMode ? 'text-slate-300' : 'text-gray-600'
                  }`}>
                    <div className={`animate-spin rounded-full h-4 w-4 border-b-2 ${
                      darkMode ? 'border-slate-400' : 'border-gray-500'
                    }`}></div>
                    <span>Analyzing...</span>
                  </div>
                )}
                {error && <span className="text-red-400 animate-pulse">{error}</span>}
              </div>
            </form>

            {gameOut && (
              <div className={`mt-8 space-y-6 ${animateResults ? 'animate-pulse' : ''}`}>
                <div className={`p-6 rounded-2xl border backdrop-blur-sm shadow-lg ${
                  darkMode 
                    ? 'bg-gradient-to-br from-slate-500/20 to-slate-600/20 border-slate-400/30' 
                    : 'bg-gradient-to-br from-gray-100/50 to-gray-200/50 border-gray-300/50'
                }`}>
                  <div className={`text-lg font-semibold mb-3 ${
                    darkMode ? 'text-slate-200' : 'text-gray-700'
                  }`}>🏆 Predicted Winner</div>
                  <div className={`text-3xl font-bold ${
                    darkMode ? 'text-white' : 'text-gray-900'
                  }`}>
                    {gameOut.winner}
                  </div>
                </div>
                
                {gameOut.probabilities && (
                  <div className="space-y-4">
                    <h3 className={`text-sm font-semibold uppercase tracking-wide ${
                      darkMode ? 'text-slate-300' : 'text-gray-600'
                    }`}>Win Probabilities</h3>
                    {Object.entries(gameOut.probabilities).map(([label, val], index) => (
                      <div key={label} className={`p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 ${
                        darkMode 
                          ? 'bg-gradient-to-r from-slate-800/50 to-slate-700/30 border-slate-500/20' 
                          : 'bg-gradient-to-r from-gray-100/50 to-gray-200/30 border-gray-300/50'
                      }`} style={{ animationDelay: `${index * 200}ms` }}>
                        <div className="flex justify-between text-sm mb-2">
                          <span className={`uppercase tracking-wide font-medium ${
                            darkMode ? 'text-slate-200' : 'text-gray-700'
                          }`}>{label}</span>
                          <span className={`font-bold ${
                            darkMode ? 'text-slate-100' : 'text-gray-800'
                          }`}>{(val * 100).toFixed(1)}%</span>
                        </div>
                        <div className={`w-full h-3 rounded-full overflow-hidden backdrop-blur-sm shadow-inner ${
                          darkMode ? 'bg-slate-700/50' : 'bg-gray-300/50'
                        }`}>
                          <span 
                            className={`block h-full rounded-full transition-all duration-1000 ease-out ${
                              darkMode 
                                ? 'bg-gradient-to-r from-slate-400 via-slate-500 to-slate-600' 
                                : 'bg-gradient-to-r from-gray-500 via-gray-600 to-gray-700'
                            }`}
                            style={{ width: `${val * 100}%` }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {gameOut.mvpCandidates?.length > 0 && (
                  <div className="space-y-4">
                    <h3 className={`text-sm font-semibold uppercase tracking-wide ${
                      darkMode ? 'text-slate-300' : 'text-gray-600'
                    }`}>MVP Candidates</h3>
                    {gameOut.mvpCandidates.map((player, i) => (
                      <div key={i} className={`p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 ${
                        darkMode 
                          ? 'bg-gradient-to-r from-slate-800/50 to-slate-700/30 border-slate-500/20' 
                          : 'bg-gradient-to-r from-gray-100/50 to-gray-200/30 border-gray-300/50'
                      }`} style={{ animationDelay: `${i * 150}ms` }}>
                        <div className="flex justify-between text-sm mb-2">
                          <span className={`uppercase tracking-wide font-medium ${
                            darkMode ? 'text-slate-200' : 'text-gray-700'
                          }`}>{player.name} ({player.teamName})</span>
                          <span className={`font-bold ${
                            darkMode ? 'text-slate-100' : 'text-gray-800'
                          }`}>{(player.probability * 100).toFixed(1)}%</span>
                        </div>
                        <div className={`w-full h-3 rounded-full overflow-hidden backdrop-blur-sm shadow-inner ${
                          darkMode ? 'bg-slate-700/50' : 'bg-gray-300/50'
                        }`}>
                          <span 
                            className={`block h-full rounded-full transition-all duration-1000 ease-out ${
                              darkMode 
                                ? 'bg-gradient-to-r from-slate-400 via-slate-500 to-slate-600' 
                                : 'bg-gradient-to-r from-gray-500 via-gray-600 to-gray-700'
                            }`}
                            style={{ width: `${player.probability * 100}%` }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {gameOut.homeTopPlayers?.length > 0 && (
                  <div className="space-y-4">
                    <h3 className={`text-sm font-semibold uppercase tracking-wide ${
                      darkMode ? 'text-slate-300' : 'text-gray-600'
                    }`}>Home Top Players</h3>
                    {gameOut.homeTopPlayers.map((player, i) => (
                      <div key={i} className={`p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 ${
                        darkMode 
                          ? 'bg-gradient-to-r from-slate-800/50 to-slate-700/30 border-slate-500/20' 
                          : 'bg-gradient-to-r from-gray-100/50 to-gray-200/30 border-gray-300/50'
                      }`} style={{ animationDelay: `${i * 150}ms` }}>
                        <div className="flex justify-between text-sm mb-2">
                          <span className={`uppercase tracking-wide font-medium ${
                            darkMode ? 'text-slate-200' : 'text-gray-700'
                          }`}>{player.name}</span>
                          <span className={`font-bold ${
                            darkMode ? 'text-slate-100' : 'text-gray-800'
                          }`}>{(player.probability * 100).toFixed(1)}%</span>
                        </div>
                        <div className={`w-full h-3 rounded-full overflow-hidden backdrop-blur-sm shadow-inner ${
                          darkMode ? 'bg-slate-700/50' : 'bg-gray-300/50'
                        }`}>
                          <span 
                            className={`block h-full rounded-full transition-all duration-1000 ease-out ${
                              darkMode 
                                ? 'bg-gradient-to-r from-slate-400 via-slate-500 to-slate-600' 
                                : 'bg-gradient-to-r from-gray-500 via-gray-600 to-gray-700'
                            }`}
                            style={{ width: `${player.probability * 100}%` }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {gameOut.awayTopPlayers?.length > 0 && (
                  <div className="space-y-4">
                    <h3 className={`text-sm font-semibold uppercase tracking-wide ${
                      darkMode ? 'text-slate-300' : 'text-gray-600'
                    }`}>Away Top Players</h3>
                    {gameOut.awayTopPlayers.map((player, i) => (
                      <div key={i} className={`p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 ${
                        darkMode 
                          ? 'bg-gradient-to-r from-slate-800/50 to-slate-700/30 border-slate-500/20' 
                          : 'bg-gradient-to-r from-gray-100/50 to-gray-200/30 border-gray-300/50'
                      }`} style={{ animationDelay: `${i * 150}ms` }}>
                        <div className="flex justify-between text-sm mb-2">
                          <span className={`uppercase tracking-wide font-medium ${
                            darkMode ? 'text-slate-200' : 'text-gray-700'
                          }`}>{player.name}</span>
                          <span className={`font-bold ${
                            darkMode ? 'text-slate-100' : 'text-gray-800'
                          }`}>{(player.probability * 100).toFixed(1)}%</span>
                        </div>
                        <div className={`w-full h-3 rounded-full overflow-hidden backdrop-blur-sm shadow-inner ${
                          darkMode ? 'bg-slate-700/50' : 'bg-gray-300/50'
                        }`}>
                          <span 
                            className={`block h-full rounded-full transition-all duration-1000 ease-out ${
                              darkMode 
                                ? 'bg-gradient-to-r from-slate-400 via-slate-500 to-slate-600' 
                                : 'bg-gradient-to-r from-gray-500 via-gray-600 to-gray-700'
                            }`}
                            style={{ width: `${player.probability * 100}%` }} 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className={`backdrop-blur-xl border rounded-3xl shadow-2xl p-8 transition-all duration-500 ${
            animateResults ? 'animate-pulse' : ''
          } ${
            darkMode 
              ? 'bg-white/5 border-white/10' 
              : 'bg-white/80 border-gray-200/50'
          }`}>
            <h2 className={`text-2xl font-semibold mb-6 bg-clip-text text-transparent ${
              darkMode 
                ? 'bg-gradient-to-r from-slate-200 to-slate-300' 
                : 'bg-gradient-to-r from-gray-700 to-gray-800'
            }`}>
              How It Works
            </h2>
            <div className={`space-y-6 text-sm ${
              darkMode ? 'text-slate-300' : 'text-gray-600'
            }`}>
              <div className={`flex items-start gap-4 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 group ${
                darkMode 
                  ? 'bg-gradient-to-r from-slate-800/30 to-slate-700/20 border-slate-500/10' 
                  : 'bg-gradient-to-r from-gray-100/30 to-gray-200/20 border-gray-300/50'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0 transition-all duration-300 group-hover:scale-110 shadow-lg ${
                  darkMode 
                    ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
                    : 'bg-gradient-to-r from-gray-500 to-gray-600'
                }`}>1</div>
                <div>
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${
                    darkMode 
                      ? 'text-slate-200 group-hover:text-slate-100' 
                      : 'text-gray-700 group-hover:text-gray-800'
                  }`}>Select League</div>
                  <div>Choose from available leagues in your dataset</div>
                </div>
              </div>
              <div className={`flex items-start gap-4 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 group ${
                darkMode 
                  ? 'bg-gradient-to-r from-slate-800/30 to-slate-700/20 border-slate-500/10' 
                  : 'bg-gradient-to-r from-gray-100/30 to-gray-200/20 border-gray-300/50'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0 transition-all duration-300 group-hover:scale-110 shadow-lg ${
                  darkMode 
                    ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
                    : 'bg-gradient-to-r from-gray-500 to-gray-600'
                }`}>2</div>
                <div>
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${
                    darkMode 
                      ? 'text-slate-200 group-hover:text-slate-100' 
                      : 'text-gray-700 group-hover:text-gray-800'
                  }`}>Pick Teams</div>
                  <div>Select home and away teams from the league</div>
                </div>
              </div>
              <div className={`flex items-start gap-4 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 group ${
                darkMode 
                  ? 'bg-gradient-to-r from-slate-800/30 to-slate-700/20 border-slate-500/10' 
                  : 'bg-gradient-to-r from-gray-100/30 to-gray-200/20 border-gray-300/50'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0 transition-all duration-300 group-hover:scale-110 shadow-lg ${
                  darkMode 
                    ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
                    : 'bg-gradient-to-r from-gray-500 to-gray-600'
                }`}>3</div>
                <div>
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${
                    darkMode 
                      ? 'text-slate-200 group-hover:text-slate-100' 
                      : 'text-gray-700 group-hover:text-gray-800'
                  }`}>Get Predictions</div>
                  <div>AI analyzes historical data to predict match outcomes</div>
                </div>
              </div>
              <div className={`flex items-start gap-4 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-105 group ${
                darkMode 
                  ? 'bg-gradient-to-r from-slate-800/30 to-slate-700/20 border-slate-500/10' 
                  : 'bg-gradient-to-r from-gray-100/30 to-gray-200/20 border-gray-300/50'
              }`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0 transition-all duration-300 group-hover:scale-110 shadow-lg ${
                  darkMode 
                    ? 'bg-gradient-to-r from-slate-400 to-slate-500' 
                    : 'bg-gradient-to-r from-gray-500 to-gray-600'
                }`}>4</div>
                <div>
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${
                    darkMode 
                      ? 'text-slate-200 group-hover:text-slate-100' 
                      : 'text-gray-700 group-hover:text-gray-800'
                  }`}>Top Players</div>
                  <div>Discover MVP candidates and top performers from both teams</div>
                </div>
              </div>
            </div>
            
            <div className={`mt-8 p-6 rounded-xl border ${
              darkMode 
                ? 'bg-gradient-to-br from-slate-800/50 to-slate-700/30 border-slate-500/20' 
                : 'bg-gradient-to-br from-gray-100/50 to-gray-200/30 border-gray-300/50'
            }`}>
              <div className={`text-sm font-semibold mb-3 ${
                darkMode ? 'text-slate-200' : 'text-gray-700'
              }`}>Model Information</div>
              <div className={`text-xs space-y-2 ${
                darkMode ? 'text-slate-300' : 'text-gray-600'
              }`}>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    darkMode ? 'bg-slate-400' : 'bg-gray-500'
                  }`}></span>
                  Trained on {gameOut?.trained_samples || 'N/A'} matches
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    darkMode ? 'bg-slate-500' : 'bg-gray-600'
                  }`}></span>
                  Uses Random Forest algorithm
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    darkMode ? 'bg-slate-600' : 'bg-gray-700'
                  }`}></span>
                  Predicts Home/Away/Draw outcomes
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    darkMode ? 'bg-slate-400' : 'bg-gray-500'
                  }`}></span>
                  Includes player performance rankings
                </div>
              </div>
            </div>
          </div>
        </section>

        <footer id="about" className={`mt-20 text-center text-sm ${
          darkMode ? 'text-slate-400' : 'text-gray-500'
        }`}>
          <div className="mb-6">
            <span className={`bg-clip-text text-transparent font-semibold ${
              darkMode 
                ? 'bg-gradient-to-r from-slate-200 to-slate-300' 
                : 'bg-gradient-to-r from-gray-700 to-gray-800'
            }`}>
              Built with React + Flask + Machine Learning
            </span>
          </div>
          <div className="flex justify-center gap-8 text-xs">
            <span className={`flex items-center gap-2 transition-colors duration-300 cursor-pointer ${
              darkMode ? 'hover:text-slate-200' : 'hover:text-gray-700'
            }`}>
              <span className="text-lg">⚽</span>
              <span>Football Analytics</span>
            </span>
            <span className={`flex items-center gap-2 transition-colors duration-300 cursor-pointer ${
              darkMode ? 'hover:text-slate-200' : 'hover:text-gray-700'
            }`}>
              <span className="text-lg">🤖</span>
              <span>AI Predictions</span>
            </span>
            <span className={`flex items-center gap-2 transition-colors duration-300 cursor-pointer ${
              darkMode ? 'hover:text-slate-200' : 'hover:text-gray-700'
            }`}>
              <span className="text-lg">📊</span>
              <span>Data Science</span>
            </span>
          </div>
        </footer>
      </main>
    </div>
  )
}