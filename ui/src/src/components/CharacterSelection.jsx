import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, Heart, Brain, Zap, Shield, Star, Search, Users } from 'lucide-react'

const CharacterSelection = ({ characters, onCharacterSelect, apiBaseUrl }) => {
  const [characterDetails, setCharacterDetails] = useState({})
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredCharacters, setFilteredCharacters] = useState(characters)

  useEffect(() => {
    setFilteredCharacters(
      characters.filter(char => 
        char.toLowerCase().includes(searchTerm.toLowerCase())
      )
    )
  }, [characters, searchTerm])

  const loadCharacterDetails = async (characterName) => {
    if (characterDetails[characterName]) return characterDetails[characterName]
    
    setLoading(true)
    try {
      const response = await fetch(`${apiBaseUrl}/api/characters/${encodeURIComponent(characterName)}/info`)
      if (response.ok) {
        const data = await response.json()
        setCharacterDetails(prev => ({
          ...prev,
          [characterName]: data
        }))
        return data
      }
    } catch (error) {
      console.error('Failed to load character details:', error)
    } finally {
      setLoading(false)
    }
    return null
  }

  const getPersonalityIcon = (traits) => {
    if (!traits || traits.length === 0) return User
    
    const trait = traits[0].toLowerCase()
    if (trait.includes('wise') || trait.includes('intelligent')) return Brain
    if (trait.includes('brave') || trait.includes('bold')) return Shield
    if (trait.includes('passionate') || trait.includes('emotional')) return Heart
    if (trait.includes('energetic') || trait.includes('active')) return Zap
    return Star
  }

  const getPersonalityColor = (traits) => {
    if (!traits || traits.length === 0) return 'var(--char-noble)'
    
    const trait = traits[0].toLowerCase()
    if (trait.includes('wise') || trait.includes('intelligent')) return 'var(--char-wise)'
    if (trait.includes('brave') || trait.includes('bold')) return 'var(--char-brave)'
    if (trait.includes('mysterious')) return 'var(--char-mysterious)'
    if (trait.includes('gentle') || trait.includes('kind')) return 'var(--char-gentle)'
    if (trait.includes('passionate') || trait.includes('emotional')) return 'var(--char-passionate)'
    if (trait.includes('cunning') || trait.includes('clever')) return 'var(--char-cunning)'
    if (trait.includes('whimsical') || trait.includes('playful')) return 'var(--char-whimsical)'
    return 'var(--char-noble)'
  }

  const CharacterCard = ({ characterName }) => {
    const [details, setDetails] = useState(null)
    const [isLoaded, setIsLoaded] = useState(false)

    useEffect(() => {
      const loadDetails = async () => {
        const data = await loadCharacterDetails(characterName)
        setDetails(data)
        setIsLoaded(true)
      }
      loadDetails()
    }, [characterName])

    const personalityTraits = details?.persona?.personality_traits || []
    const motivations = details?.persona?.motivations || []
    const IconComponent = getPersonalityIcon(personalityTraits)
    const accentColor = getPersonalityColor(personalityTraits)

    return (
      <motion.div
        layout
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ 
          y: -8,
          transition: { duration: 0.2 }
        }}
        whileTap={{ scale: 0.98 }}
        onClick={() => onCharacterSelect(characterName)}
        className="card p-6 cursor-pointer hover:glow-effect transition-all duration-300 group"
        style={{
          borderLeft: `4px solid ${accentColor}`
        }}
      >
        {/* Character Header */}
        <div className="flex items-center gap-4 mb-4">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center text-white"
            style={{ backgroundColor: accentColor }}
          >
            <IconComponent size={24} />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-primary group-hover:gradient-text transition-all duration-300">
              {characterName}
            </h3>
            <p className="text-sm text-secondary">
              {isLoaded ? 'Ready to chat' : 'Loading personality...'}
            </p>
          </div>
        </div>

        {/* Personality Traits */}
        {isLoaded && personalityTraits.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {personalityTraits.slice(0, 3).map((trait, index) => (
                <span 
                  key={index}
                  className="px-3 py-1 text-xs rounded-full glass-morphism text-secondary"
                >
                  {trait}
                </span>
              ))}
              {personalityTraits.length > 3 && (
                <span className="px-3 py-1 text-xs rounded-full glass-morphism text-muted">
                  +{personalityTraits.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Primary Motivation */}
        {isLoaded && motivations.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-secondary italic">
              "{motivations[0]}"
            </p>
          </div>
        )}

        {/* Relationships Indicator */}
        {isLoaded && details?.persona?.relationships && Object.keys(details.persona.relationships).length > 0 && (
          <div className="flex items-center gap-2 text-muted text-sm">
            <Users size={14} />
            <span>
              Knows {Object.keys(details.persona.relationships).length} other characters
            </span>
          </div>
        )}

        {/* Loading State */}
        {!isLoaded && (
          <div className="space-y-3">
            <div className="h-4 bg-bg-secondary rounded animate-pulse" />
            <div className="h-3 bg-bg-secondary rounded w-3/4 animate-pulse" />
          </div>
        )}

        {/* Hover Effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-5 transition-opacity duration-300 pointer-events-none" />
      </motion.div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h2 className="text-3xl font-bold gradient-text font-display mb-4">
          Choose Your Character
        </h2>
        <p className="text-secondary max-w-2xl mx-auto">
          Select a literary character to begin an authentic conversation. 
          Each character embodies their unique personality, knowledge, and speech patterns.
        </p>
      </motion.div>

      {/* Search */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="relative max-w-md mx-auto">
          <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search characters..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input pl-10"
          />
        </div>
      </motion.div>

      {/* Characters Grid */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        {filteredCharacters.length > 0 ? (
          filteredCharacters.map((character, index) => (
            <motion.div
              key={character}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
            >
              <CharacterCard characterName={character} />
            </motion.div>
          ))
        ) : characters.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="col-span-full text-center py-16"
          >
            <Users size={48} className="mx-auto text-muted mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Characters Available</h3>
            <p className="text-secondary">
              Please upload book data and extract characters to begin chatting.
            </p>
          </motion.div>
        ) : (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="col-span-full text-center py-16"
          >
            <Search size={48} className="mx-auto text-muted mb-4" />
            <h3 className="text-xl font-semibold mb-2">No matches found</h3>
            <p className="text-secondary">
              Try adjusting your search term to find characters.
            </p>
          </motion.div>
        )}
      </motion.div>

      {/* Stats */}
      {characters.length > 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-12 text-center text-muted text-sm"
        >
          <p>
            {filteredCharacters.length} of {characters.length} characters available
          </p>
        </motion.div>
      )}
    </div>
  )
}

export default CharacterSelection