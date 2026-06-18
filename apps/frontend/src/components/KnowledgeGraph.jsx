import { useRef, useEffect, useState } from 'react'
import * as d3 from 'd3'

export function KnowledgeGraph({ nodes, edges, onNodeClick }) {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [tooltip, setTooltip] = useState({
    show: false,
    x: 0,
    y: 0,
    data: null,
  })

  useEffect(() => {
    if (!nodes || nodes.length === 0) return

    const width = containerRef.current.clientWidth || 800
    const height = containerRef.current.clientHeight || 600

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    svg.attr('width', width).attr('height', height)

    // Zoom container
    const g = svg.append('g')

    const zoom = d3
      .zoom()
      .scaleExtent([0.3, 3])
      .on('zoom', (e) => {
        g.attr('transform', e.transform)
      })

    svg.call(zoom)

    // We must clone nodes and edges because d3 mutates them
    const simNodes = nodes.map((d) => ({ ...d }))
    const simEdges = edges.map((d) => ({ ...d }))

    // Force simulation
    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        'link',
        d3
          .forceLink(simEdges)
          .id((d) => d.id)
          .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide(30))

    // Edges
    const link = g
      .append('g')
      .attr('stroke', '#D6D3D1')
      .selectAll('line')
      .data(simEdges)
      .join('line')
      .attr('stroke-opacity', (d) =>
        Math.max(0.2, Math.min(d.weight || 0.5, 0.8))
      )
      .attr('stroke-width', (d) => Math.max(1, (d.weight || 0.5) * 3))
      .attr('stroke-dasharray', (d) => {
        if (d.relationship_type === 'conceptual_link') return '4,4'
        if (d.relationship_type === 'same_creator') return '2,6'
        return 'none'
      })

    // Nodes
    const getNodeColor = (type) => {
      if (type === 'instagram_reel' || type === 'reel' || type === 'video')
        return '#C4B5A5'
      if (type === 'pdf') return '#A8B5C4'
      if (type === 'image') return '#C4A8B5'
      if (type === 'web_page' || type === 'article') return '#B5C4A8'
      return '#D6D3D1'
    }

    const node = g
      .append('g')
      .attr('stroke', '#FFFFFF')
      .attr('stroke-width', 1.5)
      .selectAll('circle')
      .data(simNodes)
      .join('circle')
      .attr('r', (d) => Math.min(6 + (d.connection_count || 1) * 0.8, 22))
      .attr('fill', (d) => getNodeColor(d.content_type))
      .style('cursor', 'pointer')
      .on('mouseover', (event, d) => {
        setTooltip({
          show: true,
          x: event.clientX,
          y: event.clientY,
          data: d,
        })
        d3.select(event.currentTarget)
          .attr('stroke', '#A8B5C4')
          .attr('stroke-width', 2.5)
      })
      .on('mousemove', (event) => {
        setTooltip((prev) => ({ ...prev, x: event.clientX, y: event.clientY }))
      })
      .on('mouseout', (event) => {
        setTooltip({ show: false, x: 0, y: 0, data: null })
        d3.select(event.currentTarget)
          .attr('stroke', '#FFFFFF')
          .attr('stroke-width', 1.5)
      })
      .on('click', (event, d) => {
        onNodeClick(d.id)
      })
      .call(drag(simulation))

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y)

      node.attr('cx', (d) => d.x).attr('cy', (d) => d.y)
    })

    function drag(simulation) {
      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      }

      function dragged(event) {
        event.subject.fx = event.x
        event.subject.fy = event.y
      }

      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }

      return d3
        .drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    }

    return () => {
      simulation.stop()
    }
  }, [nodes, edges, onNodeClick])

  return (
    <div ref={containerRef} className='w-full h-full relative bg-[#F7F5F0]'>
      <svg ref={svgRef} className='w-full h-full' />

      {tooltip.show && tooltip.data && (
        <div
          className='fixed z-50 p-3 bg-[#FFFFFF] border border-[#E7E5E4] rounded-md pointer-events-none shadow-none transform -translate-x-1/2 -translate-y-[120%]'
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <p className='text-sm font-bold text-stone-900 mb-1 truncate max-w-xs'>
            {tooltip.data.title || 'Untitled'}
          </p>
          <div className='flex items-center gap-2 text-xs text-stone-500'>
            <span className='uppercase tracking-wider font-semibold'>
              {tooltip.data.content_type?.replace('_', ' ') || 'Unknown'}
            </span>
            <span>•</span>
            <span>{tooltip.data.connection_count || 0} connections</span>
          </div>
        </div>
      )}
    </div>
  )
}
