import { cn } from '../lib/utils'

export function PlateCard({ plate, isActive, onClick }) {
  const name = plate.name || 'Untitled Plate'
  const displayName = name.length > 24 ? name.substring(0, 24) + '...' : name
  const count = plate.item_count || 0
  const thumbnails = plate.thumbnails || []

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex-shrink-0 w-48 h-20 bg-white border rounded-lg p-3 text-left transition-all',
        isActive
          ? 'border-stone-900 shadow-sm'
          : 'border-stone-200 hover:border-stone-300'
      )}
    >
      <div className='flex justify-between items-start h-full'>
        <div className='flex flex-col h-full justify-between'>
          <span className='font-bold text-sm text-stone-900 tracking-tight'>
            {displayName}
          </span>
          <span className='text-xs text-stone-500 font-medium'>
            {count} {count === 1 ? 'item' : 'items'}
          </span>
        </div>
        <div className='flex gap-1 h-full w-10 overflow-hidden rounded-sm'>
          {thumbnails.slice(0, 3).map((thumb, i) => (
            <div key={i} className='flex-1 h-full bg-stone-100'>
              {thumb && (
                <img
                  src={thumb}
                  className='w-full h-full object-cover'
                  alt=''
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </button>
  )
}
