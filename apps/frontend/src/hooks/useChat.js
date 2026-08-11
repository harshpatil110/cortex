import { useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (content) => {
    if (!content.trim() || isStreaming) return

    const userMessage = { id: Date.now().toString(), role: 'user', content }
    setMessages((prev) => [...prev, userMessage])

    const assistantId = (Date.now() + 1).toString()
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: 'assistant', content: '', sources: [] },
    ])

    setIsStreaming(true)

    try {
      const headers = { 'Content-Type': 'application/json' }

      // Convert messages to history format required by backend
      const history = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ messages: history }),
      })

      if (!response.body) throw new Error('ReadableStream not supported')

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let done = false
      let buffer = ''

      while (!done) {
        const { value, done: readerDone } = await reader.read()
        if (readerDone) {
          done = true
          break
        }

        if (value) {
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          // The last element is either an empty string (if buffer ends with \n)
          // or an incomplete line. Pop it back to buffer.
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.trim() === '') continue
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim()
              if (dataStr === '[DONE]') {
                done = true
                break
              }
              try {
                const data = JSON.parse(dataStr)
                if (data.type === 'token') {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, content: m.content + data.text }
                        : m
                    )
                  )
                } else if (data.type === 'sources') {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantId ? { ...m, sources: data.sources } : m
                    )
                  )
                }
              } catch (e) {
                console.error('Error parsing SSE JSON:', e)
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: m.content + '\n\n_Error: Failed to fetch response._',
              }
            : m
        )
      )
    } finally {
      setIsStreaming(false)
    }
  }

  const clearChat = () => setMessages([])

  return {
    messages,
    isStreaming,
    sendMessage,
    clearChat,
  }
}
