import ReactMarkdown from 'react-markdown'
import { SourceChip } from './SourceChip'
import { cn } from '../lib/utils'

export function ChatMessage({ message, onSourceClick }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex w-full mb-6',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[85%] sm:max-w-[75%] rounded-2xl px-5 py-4',
          isUser
            ? 'bg-neutral-900 text-white rounded-br-sm'
            : 'bg-white border border-neutral-200 text-black rounded-bl-sm shadow-none'
        )}
      >
        {isUser ? (
          <p className='whitespace-pre-wrap text-sm leading-relaxed'>
            {message.content}
          </p>
        ) : (
          <div className='prose prose-sm prose-stone max-w-none prose-p:leading-relaxed prose-pre:bg-stone-50 prose-pre:border prose-pre:border-stone-200 prose-pre:text-stone-800'>
            {message.content ? (
              <ReactMarkdown>{message.content}</ReactMarkdown>
            ) : (
              <span className='flex items-center gap-1 h-5'>
                <span
                  className='w-1.5 h-1.5 bg-stone-300 rounded-full animate-bounce'
                  style={{ animationDelay: '0ms' }}
                />
                <span
                  className='w-1.5 h-1.5 bg-stone-300 rounded-full animate-bounce'
                  style={{ animationDelay: '150ms' }}
                />
                <span
                  className='w-1.5 h-1.5 bg-stone-300 rounded-full animate-bounce'
                  style={{ animationDelay: '300ms' }}
                />
              </span>
            )}
          </div>
        )}

        {/* Sources Layout */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className='mt-4 pt-4 border-t border-neutral-100'>
            <p className='text-xs font-semibold text-stone-500 uppercase tracking-wider mb-3'>
              Sources
            </p>
            <div className='flex flex-wrap gap-3'>
              {message.sources.map((source, i) => (
                <SourceChip key={i} source={source} onClick={onSourceClick} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
