import { formatDistanceToNow } from 'date-fns'
import {
  Play,
  FileText,
  Image as ImageIcon,
  Globe,
  Clock,
  ExternalLink,
} from 'lucide-react'

export function MemoryCard({
  memory,
  isSelectionMode,
  isSelected,
  onToggleSelect,
}) {
  const { content_type, ai_summary, created_at, source_url } = memory

  const thumbUrl =
    memory.thumbnail_url || memory.signed_thumbnail_url || memory.thumbnail_path

  const TypeIcon = () => {
    switch (content_type) {
      case 'reel':
      case 'video':
        return <Play className='w-3 h-3 text-white' fill='currentColor' />
      case 'pdf':
        return <FileText className='w-3 h-3 text-white' />
      case 'image':
        return <ImageIcon className='w-3 h-3 text-white' />
      case 'article':
      default:
        return <Globe className='w-3 h-3 text-white' />
    }
  }

  const title = ai_summary?.title || 'Untitled Memory'
  const abstract = ai_summary?.abstract || 'No description available.'
  const techStack = ai_summary?.tech_stack || []

  let timeAgo = ''
  try {
    const d = created_at ? new Date(created_at) : new Date()
    timeAgo = formatDistanceToNow(d, { addSuffix: true })
  } catch (e) {
    timeAgo = 'Recently'
  }

  return (
    <div
      className={`flex flex-col bg-white border rounded-lg overflow-hidden transition-all group shadow-none ${isSelectionMode ? 'cursor-pointer' : ''} ${isSelected ? 'border-stone-900 ring-1 ring-stone-900' : 'border-stone-200 hover:border-stone-300'}`}
      onClick={() => {
        if (isSelectionMode && onToggleSelect) {
          onToggleSelect()
        }
      }}
    >
      {/* Thumbnail Header */}
      <div className='relative aspect-video bg-stone-100 w-full overflow-hidden'>
        {isSelectionMode && (
          <div className='absolute top-3 right-3 z-10 bg-white/80 backdrop-blur-sm rounded p-0.5 shadow-sm border border-stone-200 flex items-center justify-center'>
            <input
              type='checkbox'
              checked={isSelected}
              readOnly
              className='w-4 h-4 rounded border-stone-300 text-stone-900 focus:ring-stone-500 pointer-events-none'
            />
          </div>
        )}
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={title}
            loading='lazy'
            className='w-full h-full object-cover'
          />
        ) : (
          <div className='w-full h-full flex items-center justify-center text-stone-300'>
            <ImageIcon className='w-8 h-8' />
          </div>
        )}

        {/* Type Badge */}
        <div className='absolute top-3 left-3 bg-stone-900/80 backdrop-blur-sm rounded-sm p-1.5 shadow-sm'>
          <TypeIcon />
        </div>

        {/* Instagram SVG overlay for reels */}
        {(content_type === 'reel' || content_type === 'video') &&
          source_url && (
            <a
              href={source_url}
              target='_blank'
              rel='noopener noreferrer'
              className='absolute top-3 right-3 bg-white/90 backdrop-blur-sm p-1.5 rounded-sm shadow-sm hover:bg-white transition-colors'
            >
              <ExternalLink className='w-4 h-4 text-[#E1306C]' />
            </a>
          )}
      </div>

      {/* Body */}
      <div className='flex flex-col flex-1 p-4'>
        <h3 className='font-display font-bold text-lg text-stone-900 leading-tight line-clamp-2 mb-2'>
          {title}
        </h3>
        <p className='text-sm text-stone-500 leading-relaxed line-clamp-2 mb-4 flex-1'>
          {abstract}
        </p>

        {/* Tech Stack */}
        {techStack && techStack.length > 0 && (
          <div className='flex flex-wrap gap-1.5 mb-4'>
            {techStack.slice(0, 3).map((tech, i) => (
              <span
                key={i}
                className='px-2 py-0.5 bg-stone-100 text-stone-700 text-xs font-medium rounded-sm border border-stone-200'
              >
                {tech}
              </span>
            ))}
            {techStack.length > 3 && (
              <span className='px-2 py-0.5 bg-transparent text-stone-500 text-xs font-medium'>
                +{techStack.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className='flex items-center text-xs text-stone-400 mt-auto pt-4 border-t border-stone-100'>
          <Clock className='w-3 h-3 mr-1.5' />
          {timeAgo}
        </div>
      </div>
    </div>
  )
}
