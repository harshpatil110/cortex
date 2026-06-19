import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { SyllabusStep } from '../components/SyllabusStep'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'
import { Spinner } from '../components/ui/Spinner'

export function SyllabusPage() {
  const { id } = useParams()
  const [activeMemoryId, setActiveMemoryId] = useState(null)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['syllabus', id],
    queryFn: async () => {
      const res = await api.get(`/api/syllabus/${id}`)
      return res.data.data
    },
  })

  const { data: activeMemory } = useQuery({
    queryKey: ['memory', activeMemoryId],
    queryFn: async () => {
      if (!activeMemoryId) return null
      const res = await api.get(`/api/memories/${activeMemoryId}`)
      return res.data
    },
    enabled: !!activeMemoryId,
  })

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-[calc(100vh-64px)] bg-[#F7F5F0]'>
        <Spinner className='w-8 h-8 text-stone-400' />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className='flex items-center justify-center h-[calc(100vh-64px)] bg-[#F7F5F0] text-stone-500'>
        Syllabus not found.
      </div>
    )
  }

  const syllabus = data.syllabus_data || {}
  const steps = syllabus.steps || []

  return (
    <div className='min-h-[calc(100vh-64px)] bg-[#F7F5F0] py-12 px-4 sm:px-6 lg:px-8'>
      <div className='max-w-3xl mx-auto'>
        <div className='mb-12'>
          <h1 className='text-3xl font-display font-bold text-stone-900 mb-3'>
            {syllabus.title || data.topic_title}
          </h1>
          <p className='text-stone-500'>
            Your personalized learning path generated from your knowledge base.
          </p>
        </div>

        {/* Timeline container */}
        <div className='relative border-l border-stone-200 ml-3 sm:ml-4 pb-8'>
          {steps.map((step, i) => (
            <SyllabusStep
              key={i}
              step={step}
              syllabusId={id}
              onClick={setActiveMemoryId}
            />
          ))}
        </div>
      </div>

      <MemoryDetailPanel
        open={!!activeMemoryId}
        memory={activeMemory}
        onClose={() => setActiveMemoryId(null)}
      />
    </div>
  )
}
