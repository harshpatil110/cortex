import { useState, useEffect } from 'react'
import { Clock, CheckCircle2, Circle } from 'lucide-react'

export function SyllabusStep({ step, syllabusId, onClick }) {
  const storageKey = `syllabus_${syllabusId}_step_${step.order}`
  const [isCompleted, setIsCompleted] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(storageKey)
    if (saved === 'true') {
      setIsCompleted(true)
    }
  }, [storageKey])

  const toggleComplete = (e) => {
    e.stopPropagation()
    const next = !isCompleted
    setIsCompleted(next)
    localStorage.setItem(storageKey, next ? 'true' : 'false')
  }

  return (
    <div className='relative pl-8 sm:pl-12 py-6 group'>
      {/* Timeline Node */}
      <button
        onClick={toggleComplete}
        className='absolute left-[-13px] top-12 bg-[#F7F5F0] z-10 text-stone-300 hover:text-stone-900 transition-colors'
      >
        {isCompleted ? (
          <CheckCircle2 className='w-6 h-6 text-stone-900 bg-[#F7F5F0] rounded-full' />
        ) : (
          <Circle className='w-6 h-6 bg-[#F7F5F0] rounded-full' />
        )}
      </button>

      {/* Card */}
      <div
        onClick={() => onClick(step.memory_id)}
        className='flex flex-col sm:flex-row bg-white border border-stone-200 rounded-xl overflow-hidden hover:border-stone-400 transition-colors cursor-pointer shadow-none'
      >
        <div className='flex-1 p-5 sm:p-6'>
          <div className='flex items-start justify-between mb-3'>
            <span className='px-2 py-1 bg-stone-100 text-stone-600 text-[10px] font-bold uppercase tracking-widest rounded-sm'>
              {step.concept_group || 'Core Concept'}
            </span>
            <span className='flex items-center text-xs font-medium text-stone-400'>
              <Clock className='w-3 h-3 mr-1.5' />
              {step.estimated_minutes} min
            </span>
          </div>
          <h3
            className={`text-lg font-display font-bold mb-3 ${isCompleted ? 'text-stone-400 line-through' : 'text-stone-900'}`}
          >
            Step {step.order}: {step.step_title}
          </h3>
          <ul className='space-y-2'>
            {step.objectives?.map((obj, i) => (
              <li
                key={i}
                className={`text-sm flex items-start ${isCompleted ? 'text-stone-400' : 'text-stone-600'}`}
              >
                <span className='mr-2 mt-1.5 w-1.5 h-1.5 bg-stone-300 rounded-full flex-shrink-0'></span>
                {obj}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
