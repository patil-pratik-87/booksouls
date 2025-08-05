import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import CharacterSelection from './components/CharacterSelection'
import ChatInterface from './components/ChatInterface'
import LoadingScreen from './components/LoadingScreen'
import { BookOpen, MessageCircle, Sparkles } from 'lucide-react'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [selectedCharacter, setSelectedCharacter] = useState(null)
  const [characters, setCharacters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [apiInitialized, setApiInitialized] = useState(false)

  useEffect(() => {
    initializeAPI()
  }, [])

  const initializeAPI = async () => {
    try {
      setLoading(true)
      
      // First, check if API is healthy
      const healthResponse = await fetch(`${API_BASE_URL}/api/health`)
      const healthData = await healthResponse.json()
      
      if (!healthData.indexer_initialized || !healthData.character_factory_initialized) {
        // Initialize the indexer and character factory
        const initResponse = await fetch(`${API_BASE_URL}/api/indexer/initialize`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({})
        })
        
        if (!initResponse.ok) {
          throw new Error('Failed to initialize API')
        }
      }
      
      // Load available characters
      await loadCharacters()
      setApiInitialized(true)
      
    } catch (err) {
      console.error('API initialization failed:', err)
      setError('Failed to connect to BookSouls API. Please ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const loadCharacters = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/characters/list`)
      if (!response.ok) throw new Error('Failed to load characters')
      
      const data = await response.json()
      setCharacters(data.available_characters || [])
    } catch (err) {
      console.error('Failed to load characters:', err)
      setError('Failed to load character data')
    }
  }

  const handleCharacterSelect = (character) => {
    setSelectedCharacter(character)
  }

  const handleBackToSelection = () => {
    setSelectedCharacter(null)
  }

  if (loading) {
    return <LoadingScreen />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card p-8 text-center max-w-md mx-auto"
        >
          <div className="text-red-400 mb-4">
            <MessageCircle size={48} className="mx-auto" />
          </div>
          <h2 className="text-xl font-semibold mb-4">Connection Error</h2>
          <p className="text-secondary mb-6">{error}</p>
          <button 
            onClick={initializeAPI}
            className="btn btn-primary"
          >
            Retry Connection
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-tertiary">
      {/* Background Pattern */}
      <div className="fixed inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        }} />
      </div>

      {/* Header */}
      <header className="relative z-10 p-6">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between max-w-6xl mx-auto"
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <BookOpen size={32} className="text-primary" />
              <Sparkles size={16} className="absolute -top-1 -right-1 text-yellow-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text font-display">BookSouls</h1>
              <p className="text-sm text-secondary">Chat with Literary Characters</p>
            </div>
          </div>
          
          {selectedCharacter && (
            <button 
              onClick={handleBackToSelection}
              className="btn btn-ghost"
            >
              ← Back to Characters
            </button>
          )}
        </motion.div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 px-4 pb-8">
        <div className="max-w-6xl mx-auto">
          <AnimatePresence mode="wait">
            {!selectedCharacter ? (
              <motion.div
                key="character-selection"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
              >
                <CharacterSelection 
                  characters={characters}
                  onCharacterSelect={handleCharacterSelect}
                  apiBaseUrl={API_BASE_URL}
                />
              </motion.div>
            ) : (
              <motion.div
                key="chat-interface"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ChatInterface 
                  character={selectedCharacter}
                  apiBaseUrl={API_BASE_URL}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 p-6 text-center text-muted text-sm">
        <p>Experience authentic conversations with your favorite literary characters</p>
      </footer>
    </div>
  )
}

export default App