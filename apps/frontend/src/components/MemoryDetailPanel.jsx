import { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import {
  X,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Code,
} from 'lucide-react'
import { Badge } from './ui/Badge'
import { CodeBlock } from './CodeBlock'
import { cn } from '../lib/utils'

// Setup react-pdf worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

export function MemoryDetailPanel({ open, onClose, memory }) {
  const [mobileTab, setMobileTab] = useState('summary') // 'media', 'summary', 'transcript'
  const [transcriptOpen, setTranscriptOpen] = useState(false)
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)

  // Manage visibility for transition
  const [visible, setVisible] = useState(open)
  const [animating, setAnimating] = useState(false)

  useEffect(() => {
    if (open) {
      setVisible(true)
      // Small delay to allow DOM to render before adding translation class
      requestAnimationFrame(() => setAnimating(true))
    } else {
      setAnimating(false)
      const timer = setTimeout(() => setVisible(false), 550)
      return () => clearTimeout(timer)
    }
  }, [open])

  if (!visible || !memory) return null

  const {
    content_type,
    ai_summary,
    created_at,
    source_url,
    transcript,
    creator_handle,
  } = memory

  const mediaUrl = memory.media_url || memory.signed_url || memory.source_url
  const title = ai_summary?.title || memory.title || 'Untitled Memory'
  const abstract = ai_summary?.abstract || memory.description || ''
  const takeaways = ai_summary?.takeaways || []
  const techStack = ai_summary?.tech_stack || []
  const difficulty = ai_summary?.difficulty || 'Intermediate'
  const codeSnippets = ai_summary?.code_snippets || []

  const handleDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages)
  }

  const renderDifficultyBadge = () => {
    switch (difficulty.toLowerCase()) {
      case 'beginner':
        return (
          <span className='px-2 py-0.5 border border-green-200 text-green-700 text-xs font-semibold rounded-sm bg-white'>
            Beginner
          </span>
        )
      case 'advanced':
        return (
          <span className='px-2 py-0.5 border border-red-200 text-red-700 text-xs font-semibold rounded-sm bg-white'>
            Advanced
          </span>
        )
      default:
        return (
          <span className='px-2 py-0.5 border border-amber-200 text-amber-700 text-xs font-semibold rounded-sm bg-white'>
            Intermediate
          </span>
        )
    }
  }

  const renderMediaViewer = () => {
    if (content_type === 'instagram_reel' || content_type === 'video') {
      return (
        <div className='flex flex-col gap-4 w-full'>
          <video
            controls
            className='w-full h-auto rounded-md bg-stone-100 border border-stone-200'
          >
            <source src={mediaUrl} type='video/mp4' />
            Your browser does not support the video tag.
          </video>
          {source_url && (
            <a
              href={source_url}
              target='_blank'
              rel='noopener noreferrer'
              className='inline-flex items-center gap-2 text-sm font-medium text-stone-600 hover:text-stone-900 transition-colors'
            >
              <ExternalLink className='w-4 h-4' />
              View Original Source
            </a>
          )}
        </div>
      )
    }

    if (content_type === 'pdf') {
      return (
        <div className='w-full bg-stone-100 border border-stone-200 rounded-md p-4 flex flex-col items-center overflow-auto h-full min-h-[500px]'>
          <Document
            file={mediaUrl}
            onLoadSuccess={handleDocumentLoadSuccess}
            className='max-w-full shadow-sm'
          >
            <Page
              pageNumber={pageNumber}
              width={400}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
          {numPages && (
            <div className='flex items-center gap-4 mt-4 text-sm text-stone-600'>
              <button
                disabled={pageNumber <= 1}
                onClick={() => setPageNumber((p) => p - 1)}
                className='hover:text-stone-900 disabled:opacity-50'
              >
                Previous
              </button>
              <span>
                Page {pageNumber} of {numPages}
              </span>
              <button
                disabled={pageNumber >= numPages}
                onClick={() => setPageNumber((p) => p + 1)}
                className='hover:text-stone-900 disabled:opacity-50'
              >
                Next
              </button>
            </div>
          )}
        </div>
      )
    }

    if (content_type === 'image') {
      return (
        <div className='w-full flex justify-center bg-stone-100 border border-stone-200 rounded-md overflow-hidden'>
          <img
            src={mediaUrl}
            alt={title}
            className='w-full h-auto object-contain max-h-[70vh]'
            style={{ touchAction: 'pinch-zoom' }}
          />
        </div>
      )
    }

    if (content_type === 'web_page' || content_type === 'article') {
      return (
        <div className='w-full p-6 bg-white border border-stone-200 rounded-md prose prose-stone max-w-none'>
          {memory.parsed_content ? (
            <div dangerouslySetInnerHTML={{ __html: memory.parsed_content }} />
          ) : (
            <p className='text-stone-500 italic'>
              No parsed content available.
            </p>
          )}
        </div>
      )
    }

    return (
      <div className='flex items-center justify-center w-full h-64 bg-stone-100 border border-stone-200 rounded-md text-stone-400'>
        <FileText className='w-8 h-8 mr-2' />
        <span className='text-sm font-medium'>No media preview available</span>
      </div>
    )
  }

  const renderSummary = () => (
    <div className='space-y-8 pb-20'>
      {/* Metadata Row */}
      <div className='flex items-center justify-between text-xs text-stone-500 pb-4 border-b border-stone-200'>
        <div className='flex items-center gap-3'>
          {creator_handle && (
            <span className='font-medium text-stone-700'>
              @{creator_handle.replace(/^@/, '')}
            </span>
          )}
          <span>
            {created_at
              ? formatDistanceToNow(new Date(created_at), { addSuffix: true })
              : 'Recently'}
          </span>
        </div>
        <div className='flex items-center gap-2'>
          <span className='uppercase tracking-wider font-semibold'>
            {content_type?.replace('_', ' ')}
          </span>
          {renderDifficultyBadge()}
        </div>
      </div>

      <h2 className='text-2xl font-display font-bold text-stone-900 leading-tight'>
        {title}
      </h2>

      {/* Summary Block */}
      {abstract && (
        <div className='p-5 bg-stone-50 border border-stone-200 rounded-md text-sm text-stone-700 leading-relaxed'>
          {abstract}
        </div>
      )}

      {/* Bullet Takeaways */}
      {takeaways?.length > 0 && (
        <div>
          <h3 className='text-xs font-semibold text-stone-500 uppercase tracking-wider mb-4'>
            Key Takeaways
          </h3>
          <ul className='space-y-4'>
            {takeaways.map((point, i) => (
              <li
                key={i}
                className='pl-4 py-1 border-l-2 border-stone-200 text-sm text-stone-700'
              >
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Code Snippets */}
      {codeSnippets?.length > 0 && (
        <div>
          <h3 className='text-xs font-semibold text-stone-500 uppercase tracking-wider mb-4 flex items-center gap-2'>
            <Code className='w-4 h-4' /> Code
          </h3>
          {codeSnippets.map((snippet, i) => (
            <CodeBlock
              key={i}
              code={snippet.code || snippet}
              language={snippet.language || 'javascript'}
            />
          ))}
        </div>
      )}

      {/* Technology Tags */}
      {techStack?.length > 0 && (
        <div>
          <h3 className='text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3'>
            Tech Stack
          </h3>
          <div className='flex flex-wrap gap-2'>
            {techStack.map((tech, i) => (
              <Badge key={i} variant='outline' className='bg-white'>
                {tech}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const renderTranscript = () => (
    <div className='w-full'>
      {transcript ? (
        <div className='prose prose-sm prose-stone max-w-none text-stone-700 leading-loose'>
          {transcript.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      ) : (
        <p className='text-sm text-stone-500 italic'>
          No transcript available for this memory.
        </p>
      )}
    </div>
  )

  return (
    <div className='fixed inset-0 z-50 flex justify-end overflow-hidden'>
      {/* Backdrop */}
      <div
        className={cn(
          'absolute inset-0 bg-stone-900/10 backdrop-blur-[2px] transition-opacity duration-500',
          animating ? 'opacity-100' : 'opacity-0'
        )}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={cn(
          'relative z-50 w-full lg:w-[70%] bg-white h-full border-l border-stone-200 flex flex-col transition-transform ease-out shadow-none',
          animating ? 'translate-x-0' : 'translate-x-full'
        )}
        style={{ transitionDuration: '550ms' }}
      >
        {/* Header */}
        <div className='flex-shrink-0 flex items-center justify-between p-4 border-b border-stone-200 bg-white'>
          <h3 className='font-display text-lg font-bold text-stone-900 truncate pr-4'>
            {title}
          </h3>
          <button
            onClick={onClose}
            className='p-2 text-stone-400 hover:text-stone-900 transition-colors'
          >
            <X className='w-5 h-5' />
          </button>
        </div>

        {/* Mobile Tab Toggle */}
        <div className='lg:hidden flex items-center border-b border-stone-200 bg-stone-50 px-4'>
          {['media', 'summary', 'transcript'].map((tab) => (
            <button
              key={tab}
              onClick={() => setMobileTab(tab)}
              className={cn(
                'flex-1 py-3 text-sm font-medium capitalize border-b-2 transition-colors',
                mobileTab === tab
                  ? 'border-stone-900 text-stone-900'
                  : 'border-transparent text-stone-500 hover:text-stone-700'
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Body Split View */}
        <div className='flex-1 overflow-hidden flex flex-col lg:flex-row'>
          {/* Left Column: Media Viewer */}
          <div
            className={cn(
              'w-full lg:w-1/2 h-full overflow-y-auto p-6 bg-[#F7F5F0] lg:border-r border-stone-200',
              mobileTab !== 'media' && 'hidden lg:block'
            )}
          >
            {renderMediaViewer()}
          </div>

          {/* Right Column: AI Analysis */}
          <div
            className={cn(
              'w-full lg:w-1/2 h-full overflow-y-auto p-6 lg:p-8 bg-white relative',
              mobileTab !== 'summary' &&
                mobileTab !== 'transcript' &&
                'hidden lg:block'
            )}
          >
            {mobileTab === 'transcript' ? renderTranscript() : renderSummary()}

            {/* Desktop Transcript Accordion */}
            <div className='hidden lg:block absolute bottom-0 left-0 right-0 bg-white border-t border-stone-200 p-4'>
              <button
                onClick={() => setTranscriptOpen(!transcriptOpen)}
                className='flex items-center justify-between w-full text-sm font-medium text-stone-700 hover:text-stone-900'
              >
                <div className='flex items-center gap-2'>
                  <FileText className='w-4 h-4' />
                  Raw Transcript
                </div>
                {transcriptOpen ? (
                  <ChevronDown className='w-4 h-4' />
                ) : (
                  <ChevronUp className='w-4 h-4' />
                )}
              </button>

              {transcriptOpen && (
                <div className='mt-4 max-h-64 overflow-y-auto pr-2'>
                  {renderTranscript()}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
