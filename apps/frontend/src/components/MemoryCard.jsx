import { formatDistanceToNow } from 'date-fns'
import { Play, FileText, Image as ImageIcon, Globe, Clock } from 'lucide-react'

export function MemoryCard({ memory }) {
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
    <div className='flex flex-col bg-white border border-stone-200 rounded-lg overflow-hidden transition-all hover:border-stone-300 group shadow-none'>
      {/* Thumbnail Header */}
      <div className='relative aspect-video bg-stone-100 w-full overflow-hidden'>
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={title}
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
              <svg
                className='w-4 h-4 text-[#E1306C]'
                viewBox='0 0 24 24'
                fill='currentColor'
              >
                <path d='M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z' />
              </svg>
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
