import { FileText, Image as ImageIcon, Video, Globe } from 'lucide-react'

export function SourceChip({ source, onClick }) {
  const thumbUrl = source.thumbnail_url || source.signed_url

  const TypeIcon = () => {
    switch (source.content_type) {
      case 'instagram_reel':
      case 'reel':
      case 'video':
        return <Video className='w-4 h-4 text-stone-400' />
      case 'pdf':
        return <FileText className='w-4 h-4 text-stone-400' />
      case 'image':
        return <ImageIcon className='w-4 h-4 text-stone-400' />
      case 'web_page':
      case 'article':
      default:
        return <Globe className='w-4 h-4 text-stone-400' />
    }
  }

  return (
    <button
      onClick={() => onClick(source.id)}
      className='flex items-center gap-3 pr-4 bg-white border border-neutral-200 rounded-md overflow-hidden hover:bg-stone-50 transition-colors shadow-none text-left w-full sm:w-64 flex-shrink-0'
    >
      <div className='w-8 h-8 flex-shrink-0 bg-stone-100 flex items-center justify-center border-r border-neutral-200'>
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={source.title}
            className='w-full h-full object-cover'
          />
        ) : (
          <TypeIcon />
        )}
      </div>
      <div className='flex-1 min-w-0 py-1'>
        <p className='text-xs font-semibold text-stone-900 truncate'>
          {source.title || 'Untitled Source'}
        </p>
        <p className='text-[10px] text-stone-500 uppercase tracking-wider truncate'>
          {source.content_type?.replace('_', ' ') || 'Memory'}
        </p>
      </div>
    </button>
  )
}
