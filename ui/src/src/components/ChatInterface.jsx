import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, User, Bot, Heart, Brain, Zap, Shield, Star, Users, RefreshCw, Loader } from 'lucide-react'

const ChatInterface = ({ character, apiBaseUrl }) => {
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [characterInfo, setCharacterInfo] = useState(null)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    loadCharacterInfo()
    // Add welcome message
    setMessages([{
      id: Date.now(),
      type: 'character',
      content: `Hello! I'm ${character}. What would you like to talk about?`,
      timestamp: new Date().toISOString(),
      character: character
    }])
  }, [character])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const loadCharacterInfo = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/characters/${encodeURIComponent(character)}/info`)
      if (response.ok) {
        const data = await response.json()
        setCharacterInfo(data)
      }
    } catch (error) {
      console.error('Failed to load character info:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
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

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)
    setIsTyping(true)

    try {
      const response = await fetch(`${apiBaseUrl}/api/characters/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_name: character,
          message: userMessage.content,
          conversation_history: messages.map(msg => ({
            role: msg.type === 'user' ? 'user' : 'assistant',
            content: msg.content
          }))
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get character response')
      }

      const data = await response.json()
      
      if (data.success) {
        // Simulate typing delay for more natural feel
        setTimeout(() => {
          const characterMessage = {
            id: Date.now() + 1,
            type: 'character',
            content: data.response,
            timestamp: new Date().toISOString(),
            character: character,
            characterInfo: data.character_info
          }
          
          setMessages(prev => [...prev, characterMessage])
          setIsTyping(false)
        }, 500 + Math.random() * 1000) // Random delay between 0.5-1.5s
      } else {
        throw new Error(data.error || 'Unknown error')
      }
    } catch (error) {
      console.error('Chat error:', error)
      setIsTyping(false)
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I had trouble responding. Please try again.',
        timestamp: new Date().toISOString()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([{
      id: Date.now(),
      type: 'character',
      content: `Hello again! I'm ${character}. What would you like to talk about?`,
      timestamp: new Date().toISOString(),
      character: character
    }])
  }

  const personalityTraits = characterInfo?.persona?.personality_traits || []
  const relationships = characterInfo?.persona?.relationships || {}
  const IconComponent = getPersonalityIcon(personalityTraits)
  const accentColor = getPersonalityColor(personalityTraits)

  const TypingIndicator = () => (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex items-center gap-3 p-4 mb-4"
    >
      <div 
        className="w-8 h-8 rounded-full flex items-center justify-center text-white flex-shrink-0"
        style={{ backgroundColor: accentColor }}
      >
        <IconComponent size={16} />
      </div>
      <div className="glass-morphism rounded-2xl p-3 max-w-xs">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              animate={{
                y: [0, -8, 0],
                opacity: [0.3, 1, 0.3]
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut"
              }}
              className="w-2 h-2 bg-secondary rounded-full"
            />
          ))}
        </div>
      </div>
    </motion.div>
  )

  const MessageBubble = ({ message }) => {
    const isUser = message.type === 'user'
    const isError = message.type === 'error'
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.3 }}
        className={`flex items-start gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}
      >
        {/* Avatar */}
        {!isUser && (
          <div 
            className="w-8 h-8 rounded-full flex items-center justify-center text-white flex-shrink-0"
            style={{ backgroundColor: isError ? 'var(--char-passionate)' : accentColor }}
          >
            {isError ? '!' : <IconComponent size={16} />}
          </div>
        )}
        
        {isUser && (
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white flex-shrink-0">
            <User size={16} />
          </div>
        )}

        {/* Message Content */}
        <div className={`max-w-lg ${isUser ? 'text-right' : ''}`}>
          <div
            className={`rounded-2xl p-4 ${
              isUser 
                ? 'bg-primary text-white ml-auto' 
                : isError
                ? 'glass-morphism border-red-400 text-red-200'
                : 'glass-morphism'
            }`}
            style={!isUser && !isError ? { borderLeft: `3px solid ${accentColor}` } : {}}
          >
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          </div>
          
          {/* Timestamp */}
          <p className="text-xs text-muted mt-2">
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </p>
          
          {/* Character emotional state */}
          {message.characterInfo?.current_emotional_state && message.characterInfo.current_emotional_state !== 'neutral' && (
            <p className="text-xs text-accent mt-1 italic">
              {character} seems {message.characterInfo.current_emotional_state}
            </p>
          )}
        </div>
      </motion.div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-200px)] flex flex-col">
      {/* Character Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card p-6 mb-6"
        style={{ borderLeft: `4px solid ${accentColor}` }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center text-white"
              style={{ backgroundColor: accentColor }}
            >
              <IconComponent size={32} />
            </div>
            <div>
              <h2 className="text-2xl font-bold gradient-text font-display">{character}</h2>
              {characterInfo && (
                <div className="mt-2">
                  <div className="flex flex-wrap gap-2 mb-2">
                    {personalityTraits.slice(0, 3).map((trait, index) => (
                      <span 
                        key={index}
                        className="px-2 py-1 text-xs rounded-full glass-morphism text-secondary"
                      >
                        {trait}
                      </span>
                    ))}
                  </div>
                  {Object.keys(relationships).length > 0 && (
                    <div className="flex items-center gap-2 text-muted text-sm">
                      <Users size={14} />
                      <span>
                        Connected to {Object.keys(relationships).length} characters
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
          
          <button 
            onClick={clearChat}
            className="btn btn-ghost"
            title="Clear chat"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </motion.div>

      {/* Chat Messages */}
      <div className="flex-1 bg-bg-chat rounded-lg p-6 overflow-y-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          <AnimatePresence>
            {isTyping && <TypingIndicator />}
          </AnimatePresence>
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-6 card p-4"
      >
        <div className="flex gap-4">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Message ${character}...`}
              className="input resize-none"
              rows="2"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="btn btn-primary self-end"
          >
            {isLoading ? (
              <Loader size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
        
        <div className="mt-3 text-xs text-muted text-center">
          Press Enter to send • Shift+Enter for new line
        </div>
      </motion.div>
    </div>
  )
}

export default ChatInterface