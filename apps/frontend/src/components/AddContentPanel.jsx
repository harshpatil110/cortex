import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQueryClient } from '@tanstack/react-query'
import {
  Plus,
  Link2,
  Upload,
  X,
  FileText,
  Film,
  Image as ImageIcon,
  Check,
  AlertCircle,
} from 'lucide-react'
import { Sheet } from './ui/Sheet'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Badge } from './ui/Badge'
import { Spinner } from './ui/Spinner'
import { useIngestionJob } from '../hooks/useIngestionJob'
import { api } from '../lib/api'
import { cn } from '../lib/utils'

const STAGES = [
  { key: 'QUEUED', label: 'Queued' },
  { key: 'DOWNLOADING', label: 'Downloading' },
  { key: 'THUMBNAIL', label: 'Generating Thumbnail' },
  { key: 'AUDIO_EXTRACT', label: 'Extracting Audio' },
  { key: 'TRANSCRIBING', label: 'Transcribing' },
  { key: 'OCR_FRAMES', label: 'OCR Processing' },
  { key: 'SYNTHESIZING', label: 'AI Synthesis' },
  { key: 'EMBEDDING', label: 'Embedding' },
  { key: 'CLUSTERING', label: 'Clustering' },
  { key: 'MAPPING_RELATIONS', label: 'Mapping Relations' },
  { key: 'COMPLETE', label: 'Complete' },
]

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function StepperItem({ stage, status }) {
  // status: 'done' | 'active' | 'pending' | 'error'
  return (
    <div className='flex items-start gap-3 relative'>
      {/* Circle */}
      <div className='flex flex-col items-center'>
        <div
          className={cn(
            'w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all',
            status === 'done' && 'bg-stone-900',
            status === 'active' &&
              'bg-white border-2 border-blue-400 ring-4 ring-blue-100 animate-pulse',
            status === 'pending' && 'bg-white border-2 border-stone-300',
            status === 'error' && 'bg-red-100 border-2 border-red-400'
          )}
        >
          {status === 'done' && (
            <Check className='w-3 h-3 text-white' strokeWidth={3} />
          )}
          {status === 'active' && (
            <div className='w-2 h-2 bg-blue-400 rounded-full' />
          )}
          {status === 'error' && (
            <AlertCircle className='w-3 h-3 text-red-600' strokeWidth={3} />
          )}
        </div>
      </div>
      {/* Label */}
      <span
        className={cn(
          'text-sm leading-5 pb-5',
          status === 'done' && 'text-stone-900 font-medium',
          status === 'active' && 'text-stone-900 font-semibold',
          status === 'pending' && 'text-stone-400',
          status === 'error' && 'text-red-600 font-medium'
        )}
      >
        {stage.label}
      </span>
    </div>
  )
}

function JobStepper({ job, onRetry }) {
  const currentIdx = STAGES.findIndex((s) => s.key === job.currentStage)

  return (
    <div className='border-t border-stone-200 pt-4 mt-4'>
      <h4 className='text-xs font-semibold tracking-wider uppercase text-stone-500 mb-4'>
        Processing Progress
      </h4>
      <div className='relative pl-1'>
        {/* Vertical line */}
        <div className='absolute left-[9px] top-2 bottom-6 w-px bg-stone-200' />
        {STAGES.map((stage, i) => {
          let status = 'pending'
          if (job.status === 'FAILED' && i === currentIdx) status = 'error'
          else if (i < currentIdx) status = 'done'
          else if (i === currentIdx && job.status !== 'FAILED')
            status = job.status === 'COMPLETE' ? 'done' : 'active'
          return <StepperItem key={stage.key} stage={stage} status={status} />
        })}
      </div>
      {job.status === 'FAILED' && (
        <div className='mt-2 p-3 bg-red-50 border border-red-200 rounded-sm'>
          <p className='text-sm text-red-600 mb-2'>{job.error}</p>
          <Button variant='secondary' size='sm' onClick={onRetry}>
            Retry
          </Button>
        </div>
      )}
    </div>
  )
}

export function AddContentPanel() {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('url')
  const [url, setUrl] = useState('')
  const [contentType, setContentType] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [lastPayload, setLastPayload] = useState(null)
  const queryClient = useQueryClient()

  const { jobs, activeCount, openJobStream, closeJobStream } = useIngestionJob()

  // URL content-type auto-detection
  const handleUrlChange = useCallback((e) => {
    const val = e.target.value
    setUrl(val)
    if (val.includes('instagram.com') || val.includes('instagr.am')) {
      setContentType('instagram_reel')
    } else if (val.length > 5) {
      setContentType('web_page')
    } else {
      setContentType(null)
    }
  }, [])

  // Dropzone
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/webp': ['.webp'],
      'video/mp4': ['.mp4'],
    },
    maxFiles: 1,
  })

  const handleSubmit = async () => {
    setIsSubmitting(true)
    try {
      let res
      if (activeTab === 'url' && url) {
        setLastPayload({ type: 'url', url, contentType })
        res = await api.post('/api/ingest/url', {
          url,
          content_type: contentType,
        })
      } else if (activeTab === 'file' && selectedFile) {
        const formData = new FormData()
        formData.append('file', selectedFile)
        setLastPayload({ type: 'file', file: selectedFile })
        res = await api.post('/api/ingest/file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      } else {
        return
      }

      const jobId = res.data?.job_id || res.data?.id
      if (jobId) {
        openJobStream(jobId)

        // Reset form
        setUrl('')
        setContentType(null)
        setSelectedFile(null)
      }
    } catch (err) {
      console.error('Ingestion submission failed:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRetry = async () => {
    if (!lastPayload) return
    setIsSubmitting(true)
    try {
      let res
      if (lastPayload.type === 'url') {
        res = await api.post('/api/ingest/url', {
          url: lastPayload.url,
          content_type: lastPayload.contentType,
        })
      } else {
        const formData = new FormData()
        formData.append('file', lastPayload.file)
        res = await api.post('/api/ingest/file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }
      const jobId = res.data?.job_id || res.data?.id
      if (jobId) openJobStream(jobId)
    } catch (err) {
      console.error('Retry failed:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Auto-close on completion
  useEffect(() => {
    const allJobs = Array.from(jobs.values())
    const lastJob = allJobs[allJobs.length - 1]
    if (lastJob?.status === 'COMPLETE') {
      queryClient.invalidateQueries({ queryKey: ['memories'] })
      const timer = setTimeout(() => {
        closeJobStream(lastJob.id)
      }, 1500)
      return () => clearTimeout(timer)
    }
  }, [jobs, closeJobStream, queryClient])

  const jobArray = Array.from(jobs.values())

  const fileIcon = () => {
    if (!selectedFile) return null
    const ext = selectedFile.name.split('.').pop().toLowerCase()
    if (ext === 'pdf') return <FileText className='w-5 h-5 text-stone-500' />
    if (['mp4'].includes(ext))
      return <Film className='w-5 h-5 text-stone-500' />
    return <ImageIcon className='w-5 h-5 text-stone-500' />
  }

  return (
    <>
      {/* FAB */}
      <button
        onClick={() => setOpen(true)}
        className='fixed bottom-8 right-8 z-40 w-14 h-14 bg-stone-900 text-white rounded-lg shadow-sm hover:bg-stone-700 transition-colors flex items-center justify-center'
      >
        <Plus className='w-6 h-6' />
        {activeCount > 0 && (
          <span className='absolute -top-1 -right-1 w-5 h-5 bg-blue-400 text-white text-[10px] font-bold rounded-full flex items-center justify-center'>
            {activeCount}
          </span>
        )}
      </button>

      {/* Sheet */}
      <Sheet open={open} onClose={() => setOpen(false)}>
        <div className='flex items-center justify-between mb-6'>
          <h2 className='font-display text-xl font-bold text-stone-900'>
            Add Content
          </h2>
          <button
            onClick={() => setOpen(false)}
            className='text-stone-400 hover:text-stone-900 transition-colors'
          >
            <X className='w-5 h-5' />
          </button>
        </div>

        {/* Tabs */}
        <div className='flex mb-6 border-b border-stone-200'>
          <button
            onClick={() => setActiveTab('url')}
            className={cn(
              'flex items-center gap-2 pb-3 px-1 mr-6 text-sm font-medium transition-colors',
              activeTab === 'url'
                ? 'border-b-2 border-stone-900 text-stone-900'
                : 'text-stone-500 hover:text-stone-700'
            )}
          >
            <Link2 className='w-4 h-4' />
            URL Link
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={cn(
              'flex items-center gap-2 pb-3 px-1 text-sm font-medium transition-colors',
              activeTab === 'file'
                ? 'border-b-2 border-stone-900 text-stone-900'
                : 'text-stone-500 hover:text-stone-700'
            )}
          >
            <Upload className='w-4 h-4' />
            Upload File
          </button>
        </div>

        {/* URL Tab */}
        {activeTab === 'url' && (
          <div className='space-y-3'>
            <div>
              <label className='block text-xs font-semibold tracking-wider uppercase text-stone-500 mb-1.5'>
                Paste a URL
              </label>
              <Input
                type='url'
                placeholder='https://www.instagram.com/reel/...'
                value={url}
                onChange={handleUrlChange}
                disabled={isSubmitting}
              />
            </div>
            {contentType && (
              <Badge
                variant={
                  contentType === 'instagram_reel' ? 'accent' : 'secondary'
                }
              >
                {contentType === 'instagram_reel'
                  ? 'Instagram Reel'
                  : 'Web Article'}
              </Badge>
            )}
            <Button
              className='w-full'
              onClick={handleSubmit}
              disabled={!url || isSubmitting}
            >
              {isSubmitting ? <Spinner className='w-4 h-4 mr-2' /> : null}
              {isSubmitting ? 'Submitting...' : 'Ingest URL'}
            </Button>
          </div>
        )}

        {/* File Tab */}
        {activeTab === 'file' && (
          <div className='space-y-3'>
            <div
              {...getRootProps()}
              className={cn(
                'p-8 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors',
                isDragActive
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-stone-300 bg-blue-50/50 hover:border-blue-300 hover:bg-blue-50'
              )}
            >
              <input {...getInputProps()} />
              <Upload
                className='w-8 h-8 text-stone-400 mx-auto mb-3'
                strokeWidth={1.5}
              />
              <p className='text-sm font-medium text-stone-700'>
                {isDragActive
                  ? 'Drop file here'
                  : 'Drag & drop or click to browse'}
              </p>
              <p className='text-xs text-stone-400 mt-1'>
                PDF, PNG, JPG, WebP, MP4
              </p>
            </div>

            {selectedFile && (
              <div className='flex items-center gap-3 p-3 bg-stone-50 border border-stone-200 rounded-sm'>
                {fileIcon()}
                <div className='flex-1 min-w-0'>
                  <p className='text-sm font-medium text-stone-900 truncate'>
                    {selectedFile.name}
                  </p>
                  <p className='text-xs text-stone-500'>
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className='text-stone-400 hover:text-stone-900'
                >
                  <X className='w-4 h-4' />
                </button>
              </div>
            )}

            <Button
              className='w-full'
              onClick={handleSubmit}
              disabled={!selectedFile || isSubmitting}
            >
              {isSubmitting ? <Spinner className='w-4 h-4 mr-2' /> : null}
              {isSubmitting ? 'Uploading...' : 'Upload & Process'}
            </Button>
          </div>
        )}

        {/* Job Steppers */}
        {jobArray.length > 0 && (
          <div className='mt-6 space-y-4'>
            {jobArray.map((job) => (
              <JobStepper key={job.id} job={job} onRetry={handleRetry} />
            ))}
          </div>
        )}
      </Sheet>
    </>
  )
}
