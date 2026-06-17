import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MemoryDetailPanel } from '../components/MemoryDetailPanel'
import { Spinner } from '../components/ui/Spinner'
import { api } from '../lib/api'

export function MemoryDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const {
    data: memory,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['memory', id],
    queryFn: async () => {
      const res = await api.get(`/api/memories/${id}`)
      return res.data
    },
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-[calc(100vh-64px)] w-full'>
        <Spinner className='w-8 h-8 text-stone-300' />
      </div>
    )
  }

  if (isError || !memory) {
    return (
      <div className='flex flex-col items-center justify-center h-[calc(100vh-64px)] w-full text-center'>
        <h2 className='text-xl font-bold text-stone-900 mb-2'>
          Memory Not Found
        </h2>
        <p className='text-stone-500 mb-6'>
          The memory you are looking for does not exist or has been deleted.
        </p>
        <button
          onClick={() => navigate(-1)}
          className='px-4 py-2 bg-stone-900 text-white text-sm font-medium rounded-md hover:bg-stone-800'
        >
          Go Back
        </button>
      </div>
    )
  }

  return (
    <MemoryDetailPanel
      open={true}
      memory={memory}
      onClose={() => navigate(-1)}
    />
  )
}
