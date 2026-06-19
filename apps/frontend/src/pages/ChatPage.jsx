import { useState, useRef, useEffect } from 'react'
import { Send, Trash2, Sparkles } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { ChatMessage } from '../components/ChatMessage'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

const SUGGESTIONS = [
  'Summarize my recent Docker notes',
  'What terminal commands have I saved?',
  'Find quotes about design minimalism',
  'Explain my machine learning architecture',
]

export function ChatPage() {
  const { messages, isStreaming, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState('')
  const [activeMemoryId, setActiveMemoryId] = useState(null)

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Fetch memory details when source is clicked
  const { data: activeMemory } = useQuery({
    queryKey: ['memory', activeMemoryId],
    queryFn: async () => {
      if (!activeMemoryId) return null
      const res = await api.get(`/api/memories/${activeMemoryId}`)
      return res.data
    },
    enabled: !!activeMemoryId,
  })

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  const handleInput = (e) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleSubmit = (forcedInput = null) => {
    const text = typeof forcedInput === 'string' ? forcedInput : input
    if (!text.trim() || isStreaming) return
    sendMessage(text)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  return (
    <div className='flex flex-col h-[calc(100vh-64px)] w-full bg-[#FAF9F6] relative'>
      {/* Header */}
      <div className='flex-shrink-0 flex items-center justify-between px-6 py-4 bg-white border-b border-neutral-200'>
        <div className='flex items-center gap-2'>
          <Sparkles className='w-5 h-5 text-stone-700' />
          <h1 className='text-lg font-display font-bold text-stone-900'>
            Cortex Chat
          </h1>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className='flex items-center gap-2 text-sm text-stone-500 hover:text-red-600 transition-colors'
          >
            <Trash2 className='w-4 h-4' />
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className='flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-8'>
        <div className='max-w-4xl mx-auto'>
          {messages.length === 0 ? (
            <div className='flex flex-col items-center justify-center h-full min-h-[400px] text-center'>
              <Sparkles className='w-12 h-12 text-stone-300 mb-6' />
              <h2 className='text-2xl font-display font-bold text-stone-800 mb-2'>
                How can I help you remember?
              </h2>
              <p className='text-stone-500 mb-8 max-w-md'>
                Ask questions about your ingested data. I&apos;ll search your
                knowledge base and provide cited answers.
              </p>

              <div className='flex flex-col sm:flex-row flex-wrap justify-center gap-3 w-full max-w-2xl'>
                {SUGGESTIONS.map((text, i) => (
                  <button
                    key={i}
                    onClick={() => handleSubmit(text)}
                    className='px-4 py-3 bg-white border border-stone-200 rounded-full text-sm font-medium text-stone-700 hover:bg-stone-50 hover:border-stone-300 transition-colors shadow-none text-left flex-1 whitespace-nowrap overflow-hidden text-ellipsis'
                  >
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className='flex flex-col pb-4'>
              {messages.map((m) => (
                <ChatMessage
                  key={m.id}
                  message={m}
                  onSourceClick={setActiveMemoryId}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Bar */}
      <div className='flex-shrink-0 bg-white border-t border-neutral-200 p-4 sm:p-6'>
        <div className='max-w-4xl mx-auto relative flex items-end'>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder='Ask Cortex anything... (Shift+Enter for new line)'
            className='w-full resize-none py-3 pl-4 pr-14 bg-stone-50 border border-stone-200 focus:border-stone-400 focus:ring-0 rounded-xl max-h-[120px] text-sm'
            rows={1}
            disabled={isStreaming}
          />
          <button
            onClick={() => handleSubmit()}
            disabled={!input.trim() || isStreaming}
            className='absolute right-2 bottom-2 p-2 bg-neutral-900 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-800 transition-colors'
          >
            <Send className='w-4 h-4' />
          </button>
        </div>
        <p className='text-center text-[10px] text-stone-400 mt-2'>
          AI answers may vary. Clicking a source citation will open its exact
          memory context.
        </p>
      </div>

      {/* Memory Detail Overlay */}
      <MemoryDetailPanel
        open={!!activeMemoryId}
        memory={activeMemory}
        onClose={() => setActiveMemoryId(null)}
      />
    </div>
  )
}
