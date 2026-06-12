import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export function usePlates() {
  return useQuery({
    queryKey: ['plates'],
    queryFn: async () => {
      const res = await api.get('/api/plates')
      return res.data
    },
    staleTime: 60000,
  })
}
