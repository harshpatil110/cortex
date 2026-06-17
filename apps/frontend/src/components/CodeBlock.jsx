import { useState, useEffect } from 'react'
import Prism from 'prismjs'
import 'prismjs/themes/prism.css'
import { Copy, Check } from 'lucide-react'

export function CodeBlock({ code, language = 'javascript' }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    Prism.highlightAll()
  }, [code, language])

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className='relative my-4 rounded-md border border-stone-200 bg-stone-50 overflow-hidden'>
      <div className='flex items-center justify-between px-4 py-2 bg-stone-100 border-b border-stone-200'>
        <span className='text-xs font-semibold text-stone-500 uppercase tracking-wider'>
          {language}
        </span>
        <button
          onClick={handleCopy}
          className='p-1.5 rounded-md text-stone-500 hover:text-stone-900 hover:bg-stone-200 transition-colors focus:outline-none'
          title='Copy code'
        >
          {copied ? (
            <Check className='w-4 h-4 text-green-600' />
          ) : (
            <Copy className='w-4 h-4' />
          )}
        </button>
      </div>
      <div className='p-4 overflow-x-auto'>
        <pre className={`language-${language} m-0 p-0 bg-transparent`}>
          <code
            className={`language-${language} font-mono text-sm text-stone-800`}
          >
            {code}
          </code>
        </pre>
      </div>
    </div>
  )
}
