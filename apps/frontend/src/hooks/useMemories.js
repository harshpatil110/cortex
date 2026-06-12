import { useInfiniteQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useMemories({ filter = 'All', plateId = null, query = '' }) {
  return useInfiniteQuery({
    queryKey: ['memories', filter, plateId, query],
    queryFn: async ({ pageParam = 0 }) => {
      const endpoint = query ? '/api/search' : '/api/memories'

      const params = {
        limit: 12,
        offset: pageParam,
      }

      if (query) params.q = query

      const typeMap = {
        Reels: 'reel',
        PDFs: 'pdf',
        Images: 'image',
        Articles: 'article',
      }

      if (filter !== 'All') {
        params.content_type = typeMap[filter] || filter.toLowerCase()
      }

      if (plateId) params.plate_id = plateId

      const res = await api.get(endpoint, { params })
      return res.data
    },
    getNextPageParam: (lastPage, allPages) => {
      const items = Array.isArray(lastPage)
        ? lastPage
        : lastPage?.data || lastPage?.results || []
      if (items.length < 12) return undefined
      return allPages.length * 12
    },
    staleTime: 60000,
  })
}
