import { useState, useEffect } from 'react'
import { useInView } from 'react-intersection-observer'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { MemoryCard } from '../components/MemoryCard'
import { PlateCard } from '../components/PlateCard'
import { useMemories } from '../hooks/useMemories'
import { usePlates } from '../hooks/usePlates'
import { Button } from '../components/ui/Button'
import { FolderHeart } from 'lucide-react'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'

const FILTERS = ['All', 'Reels', 'PDFs', 'Images', 'Articles']

function SkeletonCard() {
  return (
    <div className='flex flex-col bg-white border border-stone-200 rounded-lg overflow-hidden shadow-none'>
      <div className='aspect-video bg-stone-200 animate-pulse w-full'></div>
      <div className='p-4 space-y-4'>
        <div className='h-5 bg-stone-200 rounded-sm animate-pulse w-3/4'></div>
        <div className='space-y-2'>
          <div className='h-3 bg-stone-200 rounded-sm animate-pulse w-full'></div>
          <div className='h-3 bg-stone-200 rounded-sm animate-pulse w-5/6'></div>
        </div>
        <div className='flex gap-2'>
          <div className='h-5 w-12 bg-stone-200 rounded-sm animate-pulse'></div>
          <div className='h-5 w-16 bg-stone-200 rounded-sm animate-pulse'></div>
        </div>
        <div className='pt-4 border-t border-stone-100'>
          <div className='h-3 w-20 bg-stone-200 rounded-sm animate-pulse'></div>
        </div>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className='col-span-full py-20 flex flex-col items-center justify-center text-center'>
      <div className='w-16 h-16 bg-white border border-stone-200 rounded-full flex items-center justify-center mb-4 shadow-sm text-stone-400'>
        <FolderHeart className='w-8 h-8' strokeWidth={1.5} />
      </div>
      <h3 className='text-xl font-display font-bold text-stone-900 mb-2'>
        No memories yet
      </h3>
      <p className='text-sm text-stone-500 mb-6 max-w-sm'>
        Start building your personal AI knowledge graph by adding links,
        uploading PDFs, or capturing reels.
      </p>
      <Button>Add your first memory</Button>
    </div>
  )
}

export function DashboardPage() {
  const [activeFilter, setActiveFilter] = useState('All')
  const [activePlateId, setActivePlateId] = useState(null)
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState([])
  const [topicTitle, setTopicTitle] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeMemoryId, setActiveMemoryId] = useState(null)

  const navigate = useNavigate()
  const { ref, inView } = useInView()

  const { data: platesData, isLoading: isLoadingPlates } = usePlates()

  const {
    data: memoriesData,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useMemories({ filter: activeFilter, plateId: activePlateId })

  useEffect(() => {
    if (inView && hasNextPage) {
      fetchNextPage()
    }
  }, [inView, hasNextPage, fetchNextPage])

  const plates = platesData?.data || platesData || []

  const items =
    memoriesData?.pages?.flatMap((page) =>
      Array.isArray(page) ? page : page.data || page.results || []
    ) || []

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='font-display text-3xl font-bold tracking-tight text-stone-900 mb-2'>
            Dashboard
          </h1>
          <p className='text-sm text-stone-500'>Welcome back to your Cortex.</p>
        </div>
        <Button
          variant={isSelectionMode ? 'primary' : 'outline'}
          onClick={() => {
            setIsSelectionMode(!isSelectionMode)
            if (isSelectionMode) setSelectedIds([])
          }}
        >
          {isSelectionMode ? 'Cancel Selection' : 'Select'}
        </Button>
      </div>

      {/* Plates Row */}
      {!isLoadingPlates && plates.length > 0 && (
        <div className='space-y-3'>
          <h2 className='text-xs font-semibold tracking-wider text-stone-500 uppercase'>
            Your Plates
          </h2>
          <div className='flex gap-4 overflow-x-auto pb-4 scrollbar-hide snap-x'>
            {plates.map((plate) => (
              <PlateCard
                key={plate.id}
                plate={plate}
                isActive={activePlateId === plate.id}
                onClick={() =>
                  setActivePlateId(activePlateId === plate.id ? null : plate.id)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Filters Row */}
      <div className='flex items-center gap-6 border-b border-stone-200'>
        {FILTERS.map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className={`pb-3 text-sm transition-colors relative ${
              activeFilter === filter
                ? 'font-semibold text-stone-900 border-b-2 border-stone-900'
                : 'font-medium text-stone-500 hover:text-stone-800'
            }`}
          >
            {filter}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6'>
        {status === 'pending' ? (
          Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
        ) : items.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {items.map((memory, i) => (
              <MemoryCard
                key={memory.id || i}
                memory={memory}
                isSelectionMode={isSelectionMode}
                isSelected={selectedIds.includes(memory.id)}
                onClick={() => !isSelectionMode && setActiveMemoryId(memory.id)}
                onToggleSelect={() => {
                  setSelectedIds((prev) =>
                    prev.includes(memory.id)
                      ? prev.filter((id) => id !== memory.id)
                      : [...prev, memory.id]
                  )
                }}
              />
            ))}

            {/* Loading indicator for infinite scroll */}
            {isFetchingNextPage &&
              Array.from({ length: 3 }).map((_, i) => (
                <SkeletonCard key={`sk-${i}`} />
              ))}

            {/* Intersection observer target */}
            <div ref={ref} className='h-10 w-full col-span-full'></div>
          </>
        )}
      </div>

      {/* Floating Action Bar */}
      {isSelectionMode && selectedIds.length > 0 && (
        <div className='fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-white border border-stone-200 shadow-none px-4 py-3 flex flex-col sm:flex-row items-center gap-4 rounded-xl'>
          <span className='text-sm font-medium text-stone-700 whitespace-nowrap'>
            {selectedIds.length} selected
          </span>
          <div className='hidden sm:block h-4 w-px bg-stone-200'></div>
          <input
            type='text'
            value={topicTitle}
            onChange={(e) => setTopicTitle(e.target.value)}
            placeholder='e.g., Learn Machine Learning'
            className='text-sm border border-stone-200 rounded-md focus:border-stone-500 focus:ring-0 bg-stone-50 placeholder:text-stone-400 w-full sm:w-64 px-3 py-2'
            disabled={isGenerating}
          />
          <Button
            onClick={async () => {
              if (!topicTitle.trim() || isGenerating) return
              setIsGenerating(true)
              try {
                const res = await api.post('/api/syllabus', {
                  memory_ids: selectedIds,
                  topic_title: topicTitle,
                })
                setIsSelectionMode(false)
                setSelectedIds([])
                setTopicTitle('')
                const syllabusId = res.data?.data?.id
                if (syllabusId && syllabusId !== 'temp_id') {
                  navigate(`/syllabus/${syllabusId}`)
                } else {
                  navigate('/dashboard')
                }
              } catch (e) {
                console.error(e)
                alert('Failed to generate syllabus')
              } finally {
                setIsGenerating(false)
              }
            }}
            disabled={!topicTitle.trim() || isGenerating}
            className='w-full sm:w-auto'
          >
            {isGenerating ? 'Generating...' : 'Generate Learning Path'}
          </Button>
        </div>
      )}

      {/* Detail Panel */}
      <MemoryDetailPanel
        open={!!activeMemoryId}
        memory={items.find((m) => m.id === activeMemoryId) || null}
        onClose={() => setActiveMemoryId(null)}
      />
    </div>
  )
}
