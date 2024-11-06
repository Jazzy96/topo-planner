'use client'

import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface TopologyNode {
  alId: string
  apName: string
  parentAlId: string | null
  bStaLinkBand: '6GH' | '6GL'
  channel: string[]
  bandwidth: string[]
  ip: string
}

interface TopologyData {
  deviceArray: TopologyNode[]
}

const TopologyVisualizer: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [topologyData, setTopologyData] = useState<TopologyData | null>(null)

  useEffect(() => {
    fetchTopologyData()
  }, [])

  useEffect(() => {
    if (topologyData) {
      drawTopology()
    }
  }, [topologyData])

  const fetchTopologyData = async () => {
    try {
      const response = await fetch('/api/topology')
      const data = await response.json()
      setTopologyData(data)
    } catch (error) {
      console.error('Error fetching topology data:', error)
    }
  }

  const drawTopology = () => {
    if (!svgRef.current || !topologyData) return

    const width = 900
    const height = 650
    const margin = { top: 50, right: 50, bottom: 50, left: 50 }

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const root = d3.stratify<TopologyNode>()
      .id(d => d.alId)
      .parentId(d => d.parentAlId)
      (topologyData.deviceArray)

    const treeLayout = d3.tree<TopologyNode>()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom])

    const treeData = treeLayout(root)

    // Draw links
    svg.selectAll('.link')
      .data(treeData.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('d', d3.linkVertical<d3.HierarchyPointLink<TopologyNode>, d3.HierarchyPointNode<TopologyNode>>()
        .x(d => d.x + margin.left)
        .y(d => d.y + margin.top)
      )
      .attr('fill', 'none')
      .attr('stroke', '#999')

    // Draw nodes
    const nodes = svg.selectAll('.node')
      .data(treeData.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.x + margin.left},${d.y + margin.top})`)

    nodes.append('circle')
      .attr('r', 9)
      .attr('fill', d => {
        if (d.depth === 0) return '#2D354C'
        return d.data.bStaLinkBand === '6GH' ? '#5B77CC' : '#CE6640'
      })

    nodes.append('text')
      .attr('dy', '0.31em')
      .attr('x', d => d.children ? -12 : 12)
      .attr('text-anchor', d => d.children ? 'end' : 'start')
      .text(d => d.data.apName)

    // Add channel and bandwidth inputs
    nodes.each(function(d) {
      const node = d3.select(this)
      const addInput = (className: string, value: string, index: number, label: string) => {
        node.append('text')
          .attr('class', className)
          .attr('x', 15)
          .attr('y', 20 + index * 20)
          .text(`${label}:`)

        node.append('foreignObject')
          .attr('x', 40)
          .attr('y', 5 + index * 20)
          .attr('width', 40)
          .attr('height', 20)
          .append('xhtml:input')
          .attr('type', 'text')
          .attr('value', value)
          .on('change', function() {
            updateNodeData(d.data.alId, label.toLowerCase(), index, this.value)
          })
      }

      addInput('channel-6gh', d.data.channel[2] || '', 0, 'CH')
      addInput('bandwidth-6gh', d.data.bandwidth[2] || '', 1, 'BW')
      addInput('channel-6gl', d.data.channel[3] || '', 2, 'CH')
      addInput('bandwidth-6gl', d.data.bandwidth[3] || '', 3, 'BW')
    })
  }

  const updateNodeData = (nodeId: string, field: string, index: number, newValue: string) => {
    if (!topologyData) return

    const updatedDeviceArray = topologyData.deviceArray.map(node => {
      if (node.alId === nodeId) {
        return {
          ...node,
          [field]: [
            ...node[field as keyof TopologyNode] as string[],
            ...Array(index - (node[field as keyof TopologyNode] as string[]).length).fill(''),
            newValue
          ]
        }
      }
      return node
    })

    setTopologyData({ ...topologyData, deviceArray: updatedDeviceArray })
    saveTopologyChanges({ ...topologyData, deviceArray: updatedDeviceArray })
  }

  const saveTopologyChanges = async (updatedTopology: TopologyData) => {
    try {
      const response = await fetch('/api/update-topology', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedTopology)
      })
      const data = await response.json()
      if (data.status === 'success') {
        console.log('Topology updated successfully')
      } else {
        console.error('Error updating topology:', data.message)
      }
    } catch (error) {
      console.error('Error updating topology:', error)
    }
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>WiFi Mesh Network Topology</CardTitle>
      </CardHeader>
      <CardContent>
        <svg ref={svgRef} width="900" height="650" />
      </CardContent>
    </Card>
  )
}

export default TopologyVisualizer
