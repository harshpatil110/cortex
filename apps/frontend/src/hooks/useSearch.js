import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useSearch() {
  const [searchParams, setSearchParams] = useSearchParams()

  const query = searchParams.get('q') || ''
  const mode = searchParams.get('mode') || 'hybrid'
  const contentType = searchParams.get('content_type') || ''
  const dateFrom = searchParams.get('date_from') || ''
  const dateTo = searchParams.get('date_to') || ''
  const plateId = searchParams.get('plate_id') || ''

  // Local state for debouncing
  const [debouncedQuery, setDebouncedQuery] = useState(query)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  const { data, isLoading, error } = useQuery({
    queryKey: [
      'search',
      debouncedQuery,
      mode,
      contentType,
      dateFrom,
      dateTo,
      plateId,
    ],
    queryFn: async () => {
      if (!debouncedQuery.trim()) return { results: [] }
      const params = {
        q: debouncedQuery,
        mode,
        ...(contentType && { content_type: contentType }),
        ...(dateFrom && { date_from: dateFrom }),
        ...(dateTo && { date_to: dateTo }),
        ...(plateId && { plate_id: plateId }),
      }
      const res = await api.get('/api/search', { params })
      return res.data
    },
    enabled: debouncedQuery.trim().length > 0,
    keepPreviousData: true,
  })

  const setParam = (key, value) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    setSearchParams(newParams, { replace: true })
  }

  const setQuery = (q) => setParam('q', q)
  const setMode = (m) => setParam('mode', m)
  const setContentType = (c) => setParam('content_type', c)

  return {
    query,
    setQuery,
    mode,
    setMode,
    contentType,
    setContentType,
    dateFrom,
    dateTo,
    plateId,
    results: data?.results || [],
    isLoading,
    error,
  }
}
