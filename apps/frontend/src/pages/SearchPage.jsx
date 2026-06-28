import { useEffect, useRef } from 'react'
import { Search, X, Filter } from 'lucide-react'
import { useSearch } from '../hooks/useSearch'
import { SearchResultCard } from '../components/SearchResultCard'
import { Input } from '../components/ui/Input'

import { Badge } from '../components/ui/Badge'
import { Toast } from '../components/ui/Toast'
import { cn } from '../lib/utils'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'
import { useState } from 'react'

export function SearchPage() {
  const {
    query,
    setQuery,
    mode,
    setMode,
    contentType,
    setContentType,
    results,
    isLoading,
    error,
  } = useSearch()

  const [activeMemoryId, setActiveMemoryId] = useState(null)
  const [toastError, setToastError] = useState(null)

  useEffect(() => {
    if (error) {
      if (error.response?.status === 429) {
        setToastError(
          'Rate limit exceeded. Please slow down and try again later.'
        )
      } else {
        setToastError('An error occurred while searching.')
      }
    }
  }, [error])

  const inputRef = useRef(null)

  // Cmd/Ctrl + K shortcut to focus search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Auto-focus on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  return (
    <div className='max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8'>
      {toastError && (
        <div className='fixed top-4 left-1/2 -translate-x-1/2 z-50 w-full px-4 flex justify-center'>
          <Toast
            type='error'
            message={toastError}
            onClose={() => setToastError(null)}
          />
        </div>
      )}
      {/* Header / Search Bar */}
      <div className='mb-8'>
        <h1 className='font-display text-3xl font-bold text-stone-900 mb-6'>
          Search Cortex
        </h1>
        <div className='relative flex items-center'>
          <Search className='absolute left-4 w-5 h-5 text-stone-400' />
          <Input
            ref={inputRef}
            type='text'
            placeholder='Search your memories... (Cmd/Ctrl + K)'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className='pl-12 pr-12 py-4 text-lg w-full bg-white border-stone-300 focus:border-stone-500 rounded-xl shadow-sm'
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className='absolute right-4 p-1 rounded-full text-stone-400 hover:text-stone-900 hover:bg-stone-100 transition-colors'
            >
              <X className='w-5 h-5' />
            </button>
          )}
        </div>
      </div>

      {/* Mode Toggle */}
      <div className='flex items-center gap-6 mb-8 border-b border-stone-200'>
        {[
          { id: 'hybrid', label: 'Hybrid' },
          { id: 'semantic', label: 'Semantic' },
          { id: 'lexical', label: 'Keyword' },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={cn(
              'pb-3 text-sm font-medium transition-colors relative',
              mode === m.id
                ? 'text-stone-900 border-b-2 border-stone-900'
                : 'text-stone-500 hover:text-stone-900 border-b-2 border-transparent'
            )}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className='flex flex-col lg:flex-row gap-8'>
        {/* Left Sidebar / Filters */}
        <div className='w-full lg:w-64 flex-shrink-0 space-y-6'>
          <div>
            <div className='flex items-center gap-2 mb-3 text-stone-900 font-semibold text-sm'>
              <Filter className='w-4 h-4' />
              Filters
            </div>

            {/* Content Type Filter */}
            <div className='space-y-2'>
              <label className='text-xs font-medium text-stone-500 uppercase tracking-wider'>
                Content Type
              </label>
              <select
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
                className='w-full text-sm border-stone-200 rounded-md py-2 px-3 bg-white focus:ring-stone-500 focus:border-stone-500'
              >
                <option value=''>All Types</option>
                <option value='instagram_reel'>Instagram Reel</option>
                <option value='web_page'>Web Page</option>
                <option value='pdf'>PDF Document</option>
                <option value='video'>Video</option>
              </select>
            </div>
            {/* Add more filters here as needed */}
          </div>
        </div>

        {/* Main Column */}
        <div className='flex-1 min-w-0'>
          {/* Active Filter Chips */}
          {(contentType || mode !== 'hybrid') && (
            <div className='flex items-center gap-2 mb-4 flex-wrap'>
              <span className='text-xs text-stone-500'>Active:</span>
              {mode !== 'hybrid' && (
                <Badge
                  variant='outline'
                  className='flex items-center gap-1 bg-white'
                >
                  Mode: {mode}
                  <button
                    onClick={() => setMode('hybrid')}
                    className='hover:text-stone-900'
                  >
                    <X className='w-3 h-3' />
                  </button>
                </Badge>
              )}
              {contentType && (
                <Badge
                  variant='outline'
                  className='flex items-center gap-1 bg-white'
                >
                  Type: {contentType.replace('_', ' ')}
                  <button
                    onClick={() => setContentType('')}
                    className='hover:text-stone-900'
                  >
                    <X className='w-3 h-3' />
                  </button>
                </Badge>
              )}
            </div>
          )}

          {/* Results Area */}
          {isLoading ? (
            <div className='space-y-4'>
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className='flex w-full h-40 bg-white border border-stone-200 rounded-lg overflow-hidden animate-pulse'
                >
                  <div className='w-[160px] bg-stone-200 flex-shrink-0' />
                  <div className='flex-1 p-5 space-y-3'>
                    <div className='h-4 bg-stone-200 rounded w-1/4' />
                    <div className='h-6 bg-stone-200 rounded w-3/4' />
                    <div className='h-4 bg-stone-200 rounded w-full' />
                    <div className='h-4 bg-stone-200 rounded w-5/6' />
                  </div>
                </div>
              ))}
            </div>
          ) : query && results.length === 0 ? (
            <div className='py-12 text-center bg-white border border-stone-200 rounded-lg'>
              <Search className='w-12 h-12 text-stone-300 mx-auto mb-4' />
              <h3 className='text-lg font-medium text-stone-900 mb-2'>
                No memories found for &quot;{query}&quot;
              </h3>
              <p className='text-stone-500 mb-6'>
                Try adjusting your filters or use the Add Content button to
                ingest new data.
              </p>
            </div>
          ) : (
            <div className='space-y-4'>
              {results.map((memory) => (
                <SearchResultCard
                  key={memory.id}
                  memory={memory}
                  onClick={() => setActiveMemoryId(memory.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <MemoryDetailPanel
        open={!!activeMemoryId}
        memory={results.find((m) => m.id === activeMemoryId) || null}
        onClose={() => setActiveMemoryId(null)}
      />
    </div>
  )
}
