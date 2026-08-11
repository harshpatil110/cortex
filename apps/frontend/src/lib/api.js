import axios from 'axios'
import { supabase } from './supabase'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

api.interceptors.request.use(async (config) => {
  try {
    const { data } = (await supabase.auth.getSession()) || {}
    if (data?.session?.access_token) {
      config.headers.Authorization = `Bearer ${data.session.access_token}`
    }
  } catch (err) {
    console.error('Failed to get auth session for API request:', err)
  }
  return config
})
