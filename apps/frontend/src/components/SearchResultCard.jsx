import { formatDistanceToNow } from 'date-fns'
import {
  ExternalLink,
  FileText,
  Film,
  Image as ImageIcon,
  Link2,
} from 'lucide-react'
import { Badge } from './ui/Badge'

export function SearchResultCard({ memory }) {
  const getIcon = (type) => {
    switch (type) {
      case 'instagram_reel':
        return <ExternalLink className='w-4 h-4' />
      case 'pdf':
        return <FileText className='w-4 h-4' />
      case 'video':
        return <Film className='w-4 h-4' />
      case 'image':
        return <ImageIcon className='w-4 h-4' />
      default:
        return <Link2 className='w-4 h-4' />
    }
  }

  return (
    <div className='flex w-full bg-white border border-stone-200 rounded-lg overflow-hidden shadow-none hover:shadow-sm transition-shadow'>
      {/* Left Side: Thumbnail */}
      {memory.thumbnail_url && (
        <div className='relative w-[160px] flex-shrink-0 bg-stone-100'>
          <img
            src={memory.thumbnail_url}
            alt={memory.title}
            className='w-full h-full object-cover'
          />
          {memory.content_type === 'instagram_reel' && memory.source_url && (
            <a
              href={memory.source_url}
              target='_blank'
              rel='noopener noreferrer'
              className='absolute top-2 right-2 p-1.5 bg-black/60 rounded-full text-white hover:bg-black transition-colors'
              title='Open original Reel link'
            >
              <ExternalLink className='w-4 h-4' />
            </a>
          )}
        </div>
      )}

      {/* Right Side: Content */}
      <div className='flex flex-col flex-1 p-5 min-w-0'>
        <div className='flex items-start justify-between mb-2'>
          <div className='flex items-center gap-2 text-stone-500 mb-1'>
            {getIcon(memory.content_type)}
            <span className='text-xs font-semibold tracking-wider uppercase'>
              {memory.content_type?.replace('_', ' ')}
            </span>
            {memory.similarity_score !== undefined && (
              <Badge variant='secondary' className='ml-2'>
                {Math.round(memory.similarity_score * 100)}% Match
              </Badge>
            )}
          </div>
          {memory.created_at && (
            <span className='text-xs text-stone-400'>
              {formatDistanceToNow(new Date(memory.created_at), {
                addSuffix: true,
              })}
            </span>
          )}
        </div>

        <h3 className='text-lg font-bold text-stone-900 leading-tight mb-2 truncate'>
          {memory.title || 'Untitled Memory'}
        </h3>

        {memory.creator_handle && (
          <p className='text-sm text-stone-500 mb-3'>
            @{memory.creator_handle.replace(/^@/, '')}
          </p>
        )}

        <p className='text-sm text-stone-600 line-clamp-2 mb-4 flex-1'>
          {memory.abstract || memory.description || 'No description available.'}
        </p>

        {memory.snippet && (
          <div className='mb-4 p-3 bg-stone-50 border border-stone-100 rounded-md'>
            <p
              className='text-xs text-stone-700 italic line-clamp-2'
              dangerouslySetInnerHTML={{ __html: memory.snippet }}
            />
          </div>
        )}

        <div className='flex flex-wrap gap-2 mt-auto'>
          {memory.tags?.map((tag) => (
            <Badge key={tag} variant='outline'>
              {tag}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  )
}
