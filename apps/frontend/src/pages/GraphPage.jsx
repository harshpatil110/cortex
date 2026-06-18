import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { KnowledgeGraph } from '../components/KnowledgeGraph'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'
import { Spinner } from '../components/ui/Spinner'
import { api } from '../lib/api'

export function GraphPage() {
  const [activeMemoryId, setActiveMemoryId] = useState(null)

  // Filters
  const [activeTypes, setActiveTypes] = useState({
    video: true,
    pdf: true,
    image: true,
    web_page: true,
    article: true,
    instagram_reel: true,
    reel: true,
  })

  const { data, isLoading, isError } = useQuery({
    queryKey: ['graphData'],
    queryFn: async () => {
      const res = await api.get('/api/graph')
      return res.data
    },
  })

  // Memory Detail Fetch
  const { data: activeMemory } = useQuery({
    queryKey: ['memory', activeMemoryId],
    queryFn: async () => {
      if (!activeMemoryId) return null
      const res = await api.get(`/api/memories/${activeMemoryId}`)
      return res.data
    },
    enabled: !!activeMemoryId,
  })

  // Filter Data
  const filteredData = useMemo(() => {
    if (!data || !data.nodes) return { nodes: [], edges: [] }

    const nodes = data.nodes.filter(
      (n) => activeTypes[n.content_type] !== false
    )
    const nodeIds = new Set(nodes.map((n) => n.id))

    // Only keep edges where both source and target exist in our filtered nodes
    const edges = (data.edges || []).filter((e) => {
      const sourceId = typeof e.source === 'object' ? e.source.id : e.source
      const targetId = typeof e.target === 'object' ? e.target.id : e.target
      return nodeIds.has(sourceId) && nodeIds.has(targetId)
    })

    return { nodes, edges }
  }, [data, activeTypes])

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-[calc(100vh-64px)] w-full bg-[#F7F5F0]'>
        <Spinner className='w-8 h-8 text-stone-400' />
      </div>
    )
  }

  if (isError) {
    return (
      <div className='flex items-center justify-center h-[calc(100vh-64px)] w-full bg-[#F7F5F0] text-stone-500'>
        Failed to load knowledge graph.
      </div>
    )
  }

  const typeFilters = [
    { label: 'Videos & Reels', keys: ['video', 'instagram_reel', 'reel'] },
    { label: 'Documents', keys: ['pdf'] },
    { label: 'Images', keys: ['image'] },
    { label: 'Articles', keys: ['web_page', 'article'] },
  ]

  return (
    <div className='relative h-[calc(100vh-64px)] w-full overflow-hidden bg-[#F7F5F0]'>
      {/* Filter Overlay */}
      <div className='absolute top-4 left-4 z-10 bg-white border border-[#E7E5E4] rounded-md p-3 shadow-sm'>
        <h3 className='text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3'>
          Filter Nodes
        </h3>
        <div className='space-y-2'>
          {typeFilters.map((filter) => {
            // Group is active if ANY of its keys are active
            const isActive = filter.keys.some((k) => activeTypes[k])

            return (
              <label
                key={filter.label}
                className='flex items-center gap-2 cursor-pointer'
              >
                <input
                  type='checkbox'
                  checked={isActive}
                  onChange={() => {
                    setActiveTypes((prev) => {
                      const next = { ...prev }
                      filter.keys.forEach((k) => (next[k] = !isActive))
                      return next
                    })
                  }}
                  className='rounded border-stone-300 text-stone-900 focus:ring-stone-500'
                />
                <span className='text-sm font-medium text-stone-700'>
                  {filter.label}
                </span>
              </label>
            )
          })}
        </div>
      </div>

      <KnowledgeGraph
        nodes={filteredData.nodes}
        edges={filteredData.edges}
        onNodeClick={setActiveMemoryId}
      />

      {/* Detail Panel */}
      <MemoryDetailPanel
        open={!!activeMemoryId}
        memory={activeMemory}
        onClose={() => setActiveMemoryId(null)}
      />
    </div>
  )
}
