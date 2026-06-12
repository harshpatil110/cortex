import { useState, useCallback, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useIngestionJob() {
  const [jobs, setJobs] = useState(new Map())
  const sourcesRef = useRef(new Map())

  const updateJob = useCallback((jobId, updates) => {
    setJobs((prev) => {
      const next = new Map(prev)
      const current = next.get(jobId) || {
        id: jobId,
        stages: [],
        currentStage: null,
        status: 'QUEUED',
        error: null,
      }
      next.set(jobId, { ...current, ...updates })
      return next
    })
  }, [])

  const openJobStream = useCallback(
    (jobId) => {
      // Don't open duplicate connections
      if (sourcesRef.current.has(jobId)) return

      updateJob(jobId, {
        status: 'QUEUED',
        currentStage: 'QUEUED',
        error: null,
      })

      const es = new EventSource(`${API_BASE}/api/jobs/${jobId}/stream`)
      sourcesRef.current.set(jobId, es)

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const { stage, status, error_message } = data

          if (status === 'COMPLETE' || status === 'complete') {
            updateJob(jobId, { status: 'COMPLETE', currentStage: 'COMPLETE' })
            es.close()
            sourcesRef.current.delete(jobId)
          } else if (status === 'FAILED' || status === 'failed') {
            updateJob(jobId, {
              status: 'FAILED',
              currentStage: stage,
              error: error_message || 'Processing failed',
            })
            es.close()
            sourcesRef.current.delete(jobId)
          } else {
            updateJob(jobId, {
              status: 'PROCESSING',
              currentStage: stage || data.current_stage,
            })
          }
        } catch (e) {
          // Non-JSON heartbeat, ignore
        }
      }

      es.onerror = () => {
        es.close()
        sourcesRef.current.delete(jobId)
        updateJob(jobId, {
          status: 'FAILED',
          error: 'Lost connection to server',
        })
      }
    },
    [updateJob]
  )

  const closeJobStream = useCallback((jobId) => {
    const es = sourcesRef.current.get(jobId)
    if (es) {
      es.close()
      sourcesRef.current.delete(jobId)
    }
    setJobs((prev) => {
      const next = new Map(prev)
      next.delete(jobId)
      return next
    })
  }, [])

  const clearCompleted = useCallback(() => {
    setJobs((prev) => {
      const next = new Map(prev)
      for (const [id, job] of next) {
        if (job.status === 'COMPLETE') {
          next.delete(id)
        }
      }
      return next
    })
  }, [])

  const activeCount = Array.from(jobs.values()).filter(
    (j) => j.status === 'PROCESSING' || j.status === 'QUEUED'
  ).length

  return {
    jobs,
    activeCount,
    openJobStream,
    closeJobStream,
    clearCompleted,
  }
}
