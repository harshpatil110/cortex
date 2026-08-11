import { useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function LandingPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const sceneRef = useRef(null)
  const stackRef = useRef(null)

  // Redirect authenticated users
  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true })
    }
  }, [user, navigate])

  // Intersection Observer for Scroll Fade-Ins
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '0px',
      threshold: 0.1,
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      })
    }, observerOptions)

    const elements = document.querySelectorAll('.fade-in-up')
    elements.forEach((el) => observer.observe(el))

    return () => {
      elements.forEach((el) => observer.unobserve(el))
    }
  }, [])

  // Mouse Parallax for Hero 3D Scene
  useEffect(() => {
    const scene = sceneRef.current
    const stack = stackRef.current

    if (scene && stack) {
      const handleMouseMove = (e) => {
        const rect = scene.getBoundingClientRect()
        const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
        const y = ((e.clientY - rect.top) / rect.height) * 2 - 1

        const rotateY = x * 10
        const rotateX = -y * 10

        requestAnimationFrame(() => {
          stack.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
        })
      }

      const handleMouseLeave = () => {
        requestAnimationFrame(() => {
          stack.style.transform = `rotateX(0deg) rotateY(0deg)`
        })
      }

      scene.addEventListener('mousemove', handleMouseMove)
      scene.addEventListener('mouseleave', handleMouseLeave)

      return () => {
        scene.removeEventListener('mousemove', handleMouseMove)
        scene.removeEventListener('mouseleave', handleMouseLeave)
      }
    }
  }, [])

  if (user) return null // Avoid flashing the page before redirect

  return (
    <div className='min-h-screen flex flex-col font-sans text-stone-900 bg-[#F7F5F0]'>
      {/* TopNavBar */}
      <header className='fixed top-0 w-full z-50 bg-[#F7F5F0]/80 backdrop-blur-md border-b border-stone-200 transition-all duration-300'>
        <div className='flex justify-between items-center h-16 px-4 md:px-16 max-w-7xl mx-auto'>
          {/* Brand Logo */}
          <a
            className='font-display font-bold text-stone-900 flex items-center gap-2'
            href='#'
          >
            <span className='material-symbols-outlined text-[24px]'>
              psychology
            </span>
            Cortex
          </a>
          {/* Navigation Links */}
          <nav
            aria-label='Main Navigation'
            className='hidden md:flex gap-8 items-center'
          >
            <a
              className='text-stone-500 text-xs font-semibold uppercase tracking-widest hover:text-stone-900 transition-colors duration-200'
              href='#process'
            >
              Process
            </a>
            <a
              className='text-stone-500 text-xs font-semibold uppercase tracking-widest hover:text-stone-900 transition-colors duration-200'
              href='#architecture'
            >
              Architecture
            </a>
            <a
              className='text-stone-500 text-xs font-semibold uppercase tracking-widest hover:text-stone-900 transition-colors duration-200'
              href='#teaser'
            >
              Teaser
            </a>
          </nav>
          {/* Trailing Action */}
          <Link
            to='/auth'
            className='bg-stone-900 text-white text-xs font-semibold uppercase tracking-widest px-6 py-2 rounded-sm hover:bg-black transition-colors shadow-soft hidden md:block'
          >
            Enter Engine
          </Link>
          {/* Mobile Menu Toggle */}
          <button className='md:hidden text-stone-900'>
            <span className='material-symbols-outlined'>menu</span>
          </button>
        </div>
      </header>

      {/* Main Content Canvas */}
      <main className='flex-grow pt-24 pb-32 flex flex-col gap-32'>
        {/* Section 1: Hero */}
        <section className='max-w-7xl mx-auto px-4 md:px-16 w-full grid grid-cols-1 md:grid-cols-2 gap-16 items-center min-h-[716px]'>
          {/* Left: Typography & Actions */}
          <div className='flex flex-col gap-6 fade-in-up' id='hero-content'>
            <span className='text-xs font-semibold uppercase tracking-widest text-stone-500 flex items-center gap-2'>
              <span className='w-8 h-[1px] bg-stone-300 inline-block'></span>
              THE PERSONAL AI MEMORY ENGINE
            </span>
            <h1 className='font-sans text-[48px] md:text-[64px] font-[900] leading-[1.05] tracking-tight text-stone-900'>
              Never lose a thought.
              <br />
              Ever again.
            </h1>
            <p className='font-display text-stone-500 max-w-lg text-[22px] md:text-[24px]'>
              Capture, connect, and retrieve your digital life with
              uncompromising speed.
            </p>
            <div className='flex flex-wrap gap-4 mt-4'>
              <Link
                to='/auth'
                className='bg-stone-900 text-white text-xs font-semibold uppercase tracking-widest px-8 py-3 rounded-sm hover:bg-black transition-colors shadow-soft inline-block text-center'
              >
                Start Building
              </Link>
              <a
                href='#architecture'
                className='bg-white text-stone-900 border border-stone-200 text-xs font-semibold uppercase tracking-widest px-8 py-3 rounded-sm hover:bg-stone-50 transition-colors shadow-soft inline-block text-center'
              >
                View Architecture
              </a>
            </div>
          </div>
          {/* Right: 3D Mouse-tracking card stack */}
          <div
            ref={sceneRef}
            className='relative h-[400px] w-full perspective-1200 hidden md:block'
            id='hero-3d-scene'
          >
            <div
              ref={stackRef}
              className='absolute inset-0 flex items-center justify-center transform-style-3d transition-transform duration-700 ease-out'
              id='card-stack'
            >
              {/* Card 1 */}
              <div className='absolute surface-card shadow-soft p-6 w-[280px] h-[320px] rounded-sm transform translate-z-[-60px] translate-x-12 translate-y-[-20px] rotate-6 opacity-60'>
                <div className='w-full h-32 bg-stone-100 rounded-sm mb-4 relative overflow-hidden group'>
                  <div className='absolute inset-0 bg-stone-200 animate-pulse'></div>
                  <span className='material-symbols-outlined absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-stone-500 text-4xl group-hover:scale-110 transition-transform'>
                    play_circle
                  </span>
                </div>
                <div className='text-xs font-semibold uppercase tracking-widest text-stone-500 mb-2'>
                  Video Insight
                </div>
                <div className='h-2 w-3/4 bg-stone-100 rounded-sm mb-2'></div>
                <div className='h-2 w-1/2 bg-stone-100 rounded-sm'></div>
              </div>
              {/* Card 2 */}
              <div className='absolute surface-card shadow-soft p-6 w-[280px] h-[320px] rounded-sm transform translate-z-[-30px] translate-x-6 translate-y-[-10px] rotate-3 opacity-80 border-l-2 border-l-blue-300'>
                <div className='flex items-center gap-3 mb-6 border-b border-stone-200 pb-4'>
                  <span className='material-symbols-outlined text-red-500'>
                    picture_as_pdf
                  </span>
                  <div className='text-xs font-semibold uppercase tracking-widest text-stone-900'>
                    Research_Q3.pdf
                  </div>
                </div>
                <p className='text-sm text-stone-500 line-clamp-4'>
                  &quot;The synthesis of contextual memory architectures
                  requires a foundational shift in how we index semantic drift
                  over time...&quot;
                </p>
                <div className='mt-4 flex gap-2'>
                  <span className='bg-blue-200 text-stone-900 text-[10px] font-semibold uppercase tracking-widest px-2 py-1 rounded-sm'>
                    SEMANTIC
                  </span>
                </div>
              </div>
              {/* Card 3 */}
              <div className='absolute surface-card shadow-hover p-8 w-[300px] h-[340px] rounded-sm transform translate-z-0 transition-shadow duration-300 z-10 border-l-2 border-l-blue-300'>
                <div className='flex justify-between items-start mb-6'>
                  <span className='text-xs font-semibold uppercase tracking-widest text-stone-500'>
                    Quick Note
                  </span>
                  <span className='text-xs font-semibold uppercase tracking-widest text-stone-500'>
                    Just now
                  </span>
                </div>
                <p className='text-base text-stone-900 font-medium leading-relaxed mb-6'>
                  Remind me to connect the new ingestion pipeline to the local
                  ChromaDB instance before Thursday&apos;s review.
                </p>
                <div className='w-full bg-stone-50 p-4 border border-stone-200 rounded-sm'>
                  <div className='flex items-center gap-2 text-stone-500'>
                    <span className='material-symbols-outlined text-sm'>
                      auto_awesome
                    </span>
                    <span className='text-xs font-semibold uppercase tracking-widest text-stone-500'>
                      Cortex Extracted: Task
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Pipeline Architecture */}
        <section
          className='max-w-7xl mx-auto px-4 md:px-16 w-full relative'
          id='architecture'
        >
          <div className='text-center mb-16 fade-in-up'>
            <h2 className='text-3xl font-bold text-stone-900 mb-4'>
              The Ingestion Architecture
            </h2>
            <p className='text-base text-stone-500 max-w-2xl mx-auto'>
              A rigorously structured pipeline designed to consume, normalize,
              and spatially map heterogeneous data streams.
            </p>
          </div>
          {/* Pipeline Grid */}
          <div className='grid grid-cols-1 md:grid-cols-3 gap-8 relative fade-in-up delay-200'>
            {/* Connecting Line */}
            <div className='hidden md:block absolute top-1/2 left-0 w-full h-[1px] bg-stone-200 z-0 transform -translate-y-1/2'>
              <svg className='absolute top-[-0.5px]' height='2' width='100%'>
                <line
                  fill='none'
                  stroke='#a8a29e'
                  strokeDasharray='4 4'
                  strokeWidth='1'
                  x1='0'
                  x2='100%'
                  y1='1'
                  y2='1'
                ></line>
              </svg>
            </div>

            {/* Step 1 */}
            <div className='surface-card p-8 rounded-sm relative z-10 border-2 border-dashed border-blue-200 bg-white/80 backdrop-blur-sm flex flex-col justify-between h-[300px] group shadow-soft hover:shadow-md transition-shadow'>
              <div>
                <div className='text-xs font-semibold uppercase tracking-widest text-stone-500 mb-2'>
                  01. Ingest
                </div>
                <h3 className='text-base font-bold mb-4'>
                  Multi-modal Capture
                </h3>
                <p className='text-sm text-stone-500'>
                  Drag and drop PDFs, paste URLs, or sync Notion pages. The
                  engine normalizes all inputs into raw markdown.
                </p>
              </div>
              <div className='flex items-center justify-center h-16 w-full border border-stone-200 rounded-sm bg-stone-50 group-hover:bg-blue-50 transition-colors cursor-pointer'>
                <span className='material-symbols-outlined text-stone-400 group-hover:text-blue-500'>
                  upload_file
                </span>
              </div>
            </div>
            {/* Step 2 */}
            <div className='surface-card p-6 rounded-sm relative z-10 shadow-soft h-[300px] flex flex-col justify-between bg-white overflow-hidden'>
              <div>
                <div className='text-xs font-semibold uppercase tracking-widest text-stone-500 mb-2'>
                  02. Synthesize
                </div>
                <h3 className='text-base font-bold mb-4'>Vector Embedding</h3>
              </div>
              <div className='bg-stone-50 p-4 border border-stone-200 rounded-sm overflow-x-auto'>
                <pre className='code-snippet'>
                  <code>
                    <span className='code-keyword'>def</span>{' '}
                    process_memory(text):
                    <br />
                    <span className='code-comment'># Generate embeddings</span>
                    <br />
                    vector = embed_model.encode(text)
                    <br />
                    <br />
                    <span className='code-keyword'>return</span>{' '}
                    db.collection.add(
                    <br />
                    embeddings=[vector],
                    <br />
                    documents=[text]
                    <br />)
                  </code>
                </pre>
              </div>
            </div>
            {/* Step 3 */}
            <div className='surface-card p-8 rounded-sm relative z-10 shadow-soft h-[300px] flex flex-col justify-between bg-white border-l-2 border-l-stone-900'>
              <div>
                <div className='text-xs font-semibold uppercase tracking-widest text-stone-500 mb-2'>
                  03. Query
                </div>
                <h3 className='text-base font-bold mb-4'>Semantic Retrieval</h3>
                <p className='text-sm text-stone-500'>
                  Ask natural questions. The engine retrieves exact context and
                  synthesizes citations instantly.
                </p>
              </div>
              <div className='relative w-full'>
                <span className='material-symbols-outlined absolute left-3 top-1/2 transform -translate-y-1/2 text-stone-400 text-sm'>
                  search
                </span>
                <input
                  className='w-full pl-9 pr-4 py-3 border border-stone-200 rounded-sm text-sm focus:border-stone-900 focus:ring-0 outline-none transition-colors bg-white'
                  placeholder='What did I read about...'
                  type='text'
                />
              </div>
            </div>
          </div>
        </section>

        {/* Section 3: Knowledge Graph */}
        <section className='max-w-7xl mx-auto px-4 md:px-16 w-full relative pt-16'>
          <div className='grid grid-cols-1 md:grid-cols-12 gap-8 h-auto md:h-[600px]'>
            <div className='md:col-span-4 flex flex-col justify-center gap-6 pr-8 fade-in-up'>
              <h2 className='text-3xl font-bold text-stone-900 leading-tight'>
                Your mind, mapped.
              </h2>
              <p className='text-base text-stone-500'>
                Every piece of data ingested by Cortex is spatially related to
                existing memories. The knowledge graph isn&apos;t just a
                visualization; it&apos;s the core navigation paradigm.
              </p>
              <ul className='space-y-4 mt-4'>
                <li className='flex items-start gap-3'>
                  <span className='material-symbols-outlined text-stone-400 text-[20px] mt-1'>
                    line_end_circle
                  </span>
                  <div>
                    <span className='text-xs font-semibold uppercase tracking-widest block mb-1'>
                      Implicit Connections
                    </span>
                    <span className='text-sm text-stone-500'>
                      AI automatically clusters semantically similar concepts.
                    </span>
                  </div>
                </li>
                <li className='flex items-start gap-3'>
                  <span className='material-symbols-outlined text-stone-400 text-[20px] mt-1'>
                    share
                  </span>
                  <div>
                    <span className='text-xs font-semibold uppercase tracking-widest block mb-1'>
                      Explicit Links
                    </span>
                    <span className='text-sm text-stone-500'>
                      Manually bind nodes to force structural relationships.
                    </span>
                  </div>
                </li>
              </ul>
            </div>
            <div className='md:col-span-8 surface-card shadow-soft rounded-sm relative overflow-hidden bg-white flex items-center justify-center p-8 min-h-[400px] border border-stone-200 group fade-in-up delay-200'>
              <div className='absolute inset-0 bg-grid-pattern opacity-50'></div>
              <div className='relative w-full h-full max-w-[500px] aspect-square mx-auto flex items-center justify-center perspective-1200'>
                <div className='relative w-full h-full animate-[spin_60s_linear_infinite] transform-style-3d group-hover:[animation-play-state:paused]'>
                  <div className='absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 rounded-full bg-[#1C1917] shadow-lg flex items-center justify-center z-20 cursor-pointer peer'>
                    <span className='material-symbols-outlined text-white'>
                      drive_file_rename
                    </span>
                  </div>
                  <svg className='absolute inset-0 w-full h-full z-0 overflow-visible'>
                    <line
                      stroke='#D6D3D1'
                      strokeWidth='1.5'
                      x1='50%'
                      x2='20%'
                      y1='50%'
                      y2='30%'
                    ></line>
                    <line
                      stroke='#D6D3D1'
                      strokeWidth='1.5'
                      x1='50%'
                      x2='80%'
                      y1='50%'
                      y2='25%'
                    ></line>
                    <line
                      stroke='#D6D3D1'
                      strokeWidth='1.5'
                      x1='50%'
                      x2='75%'
                      y1='50%'
                      y2='75%'
                    ></line>
                    <line
                      stroke='#D6D3D1'
                      strokeWidth='1.5'
                      x1='50%'
                      x2='25%'
                      y1='50%'
                      y2='80%'
                    ></line>
                    <line
                      stroke='#E7E5E4'
                      strokeDasharray='4'
                      strokeWidth='1'
                      x1='20%'
                      x2='25%'
                      y1='30%'
                      y2='80%'
                    ></line>
                    <line
                      stroke='#E7E5E4'
                      strokeDasharray='4'
                      strokeWidth='1'
                      x1='80%'
                      x2='75%'
                      y1='25%'
                      y2='75%'
                    ></line>
                  </svg>
                  <div className='absolute top-[30%] left-[20%] transform -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-[#C4B5A5] shadow-sm z-10 cursor-pointer hover:scale-110 transition-transform flex items-center justify-center group/node'>
                    <span className='material-symbols-outlined text-white text-[16px]'>
                      menu_book
                    </span>
                    <div className='absolute bottom-full mb-2 bg-white border border-stone-200 shadow-soft px-3 py-2 rounded-sm opacity-0 group-hover/node:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50'>
                      <span className='text-xs font-semibold uppercase tracking-widest text-stone-900 block'>
                        Philosophy readings
                      </span>
                    </div>
                  </div>
                  <div className='absolute top-[25%] left-[80%] transform -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-[#A8B5C4] shadow-sm z-10 cursor-pointer hover:scale-110 transition-transform flex items-center justify-center group/node'>
                    <span className='material-symbols-outlined text-white text-[18px]'>
                      code
                    </span>
                    <div className='absolute bottom-full mb-2 bg-white border border-stone-200 shadow-soft px-3 py-2 rounded-sm opacity-0 group-hover/node:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50'>
                      <span className='text-xs font-semibold uppercase tracking-widest text-stone-900 block'>
                        Python Architecture
                      </span>
                    </div>
                  </div>
                  <div className='absolute top-[75%] left-[75%] transform -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#C4A8B5] shadow-sm z-10 cursor-pointer hover:scale-110 transition-transform group/node'>
                    <div className='absolute top-full mt-2 bg-white border border-stone-200 shadow-soft px-3 py-2 rounded-sm opacity-0 group-hover/node:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50'>
                      <span className='text-xs font-semibold uppercase tracking-widest text-stone-900 block'>
                        Design Inspiration
                      </span>
                    </div>
                  </div>
                  <div className='absolute top-[80%] left-[25%] transform -translate-x-1/2 -translate-y-1/2 w-14 h-14 rounded-full bg-[#B5C4A8] shadow-sm z-10 cursor-pointer hover:scale-110 transition-transform flex items-center justify-center group/node border-2 border-white'>
                    <span className='material-symbols-outlined text-white text-[20px]'>
                      lightbulb
                    </span>
                    <div className='absolute top-full mt-2 bg-white border border-stone-200 shadow-soft px-3 py-2 rounded-sm opacity-0 group-hover/node:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50'>
                      <span className='text-xs font-semibold uppercase tracking-widest text-stone-900 block'>
                        Startup Ideas
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: RAG Chat UI */}
        <section
          className='max-w-7xl mx-auto px-4 md:px-16 w-full relative pt-16 flex flex-col items-center'
          id='process'
        >
          <div className='text-center mb-12 fade-in-up'>
            <span className='text-xs font-semibold uppercase tracking-widest text-stone-500 block mb-4'>
              Retrieval Augmented Generation
            </span>
            <h2 className='text-3xl font-bold text-stone-900'>
              Talk to your memories.
            </h2>
          </div>
          <div className='w-full max-w-3xl surface-card rounded-sm shadow-soft overflow-hidden fade-in-up border-t-4 border-t-stone-900 delay-150'>
            <div className='border-b border-stone-200 bg-stone-50 px-6 py-4 flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <span className='material-symbols-outlined text-stone-600'>
                  forum
                </span>
                <span className='text-xs font-semibold uppercase tracking-widest text-stone-900'>
                  Query Engine Active
                </span>
              </div>
              <span className='w-2 h-2 rounded-full bg-blue-400 animate-pulse'></span>
            </div>
            <div className='p-6 md:p-8 flex flex-col gap-8 bg-white min-h-[300px]'>
              <div className='flex justify-end'>
                <div className='bg-stone-50 px-6 py-4 rounded-sm border border-stone-200 max-w-[80%]'>
                  <p className='text-base text-stone-800'>
                    Summarize my notes on Japanese spatial minimalism and how it
                    applies to UI design.
                  </p>
                </div>
              </div>
              <div className='flex justify-start'>
                <div className='bg-white border border-stone-200 border-l-2 border-l-blue-300 shadow-sm px-6 py-5 rounded-sm max-w-[90%] flex flex-col gap-4'>
                  <div className='flex items-center gap-2 text-blue-600 mb-1'>
                    <span className='material-symbols-outlined text-[16px]'>
                      psychology
                    </span>
                    <span className='text-xs font-semibold uppercase tracking-widest'>
                      Cortex Synthesized
                    </span>
                  </div>
                  <p className='text-base text-stone-800 leading-relaxed'>
                    Based on your notes, Japanese spatial
                    minimalism—specifically the concept of{' '}
                    <strong>&quot;Ma&quot; (negative space)</strong>—treats
                    emptiness not as an absence, but as a functional structural
                    element.
                    <br />
                    <br />
                    In UI design, you noted this translates to using generous,
                    deliberate whitespace to guide cognitive flow, rather than
                    filling screens with data. It creates an environment of
                    &quot;quiet intelligence.&quot;
                  </p>
                  <div className='flex flex-wrap gap-2 mt-2 pt-4 border-t border-stone-100'>
                    <span className='bg-blue-200 text-stone-900 text-xs font-semibold uppercase tracking-widest px-3 py-1.5 rounded-sm flex items-center gap-1 cursor-pointer hover:bg-blue-300 transition-colors'>
                      <span className='material-symbols-outlined text-[14px]'>
                        description
                      </span>
                      Design_Theory_Notes.md
                    </span>
                    <span className='bg-blue-200 text-stone-900 text-xs font-semibold uppercase tracking-widest px-3 py-1.5 rounded-sm flex items-center gap-1 cursor-pointer hover:bg-blue-300 transition-colors'>
                      <span className='material-symbols-outlined text-[14px]'>
                        link
                      </span>
                      Architecture of Ma (Web Clip)
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div className='p-4 border-t border-stone-200 bg-stone-50'>
              <div className='relative flex items-center'>
                <input
                  className='w-full bg-white border border-stone-200 rounded-sm py-3 pl-4 pr-12 text-sm text-stone-400 cursor-not-allowed'
                  disabled
                  placeholder='Ask Cortex...'
                  type='text'
                />
                <button
                  className='absolute right-3 text-stone-400 cursor-not-allowed'
                  disabled
                >
                  <span className='material-symbols-outlined'>send</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className='w-full py-12 bg-stone-50 border-t border-stone-200 mt-auto'>
        <div className='flex flex-col md:flex-row justify-between items-center px-4 md:px-16 max-w-7xl mx-auto gap-4'>
          <div className='text-xs font-semibold uppercase tracking-widest text-stone-900'>
            Cortex © 2026
          </div>
          <nav className='flex gap-4'>
            <span className='text-stone-500 text-xs font-semibold uppercase tracking-widest'>
              Built with FastAPI, React &amp; ChromaDB
            </span>
          </nav>
        </div>
      </footer>
    </div>
  )
}
