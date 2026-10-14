import React, { useState } from 'react'
import {
  GripVertical,
  ArrowUp,
  ArrowDown,
  RotateCcw,
  Sliders,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

export interface DashboardWidgetConfig {
  id: string
  title: string
  ariaLabel?: string
  icon: React.ReactNode
  colSpan?: string
  component: React.ReactNode
}

interface DraggableWidgetGridProps {
  initialWidgets: DashboardWidgetConfig[]
  className?: string
}

export function DraggableWidgetGrid({
  initialWidgets,
  className,
}: DraggableWidgetGridProps) {
  // Store only widget order in in-memory React state
  const defaultOrder = initialWidgets.map((w) => w.id)
  const [order, setOrder] = useState<string[]>(defaultOrder)
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const [dragOverId, setDragOverId] = useState<string | null>(null)

  // Map of widgets by ID for quick O(1) lookup with latest props
  const widgetMap = new Map<string, DashboardWidgetConfig>()
  initialWidgets.forEach((w) => widgetMap.set(w.id, w))

  // Ensure any newly added widgets exist in the order list
  const currentOrder = [
    ...order.filter((id) => widgetMap.has(id)),
    ...defaultOrder.filter((id) => !order.includes(id)),
  ]

  // Reorder helper
  const reorderWidgets = (fromIndex: number, toIndex: number) => {
    if (fromIndex === toIndex || toIndex < 0 || toIndex >= currentOrder.length) return
    const updated = [...currentOrder]
    const [moved] = updated.splice(fromIndex, 1)
    updated.splice(toIndex, 0, moved)
    setOrder(updated)
  }

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', id)
    setDraggedId(id)
  }

  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedId !== null && draggedId !== id) {
      setDragOverId(id)
    }
  }

  const handleDragLeave = () => {
    setDragOverId(null)
  }

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    const sourceId = draggedId || e.dataTransfer.getData('text/plain')
    if (sourceId && sourceId !== targetId) {
      const fromIndex = currentOrder.indexOf(sourceId)
      const toIndex = currentOrder.indexOf(targetId)
      if (fromIndex !== -1 && toIndex !== -1) {
        reorderWidgets(fromIndex, toIndex)
      }
    }
    setDraggedId(null)
    setDragOverId(null)
  }

  const handleDragEnd = () => {
    setDraggedId(null)
    setDragOverId(null)
  }

  // Keyboard accessibility controls
  const handleMoveUp = (index: number) => {
    reorderWidgets(index, index - 1)
  }

  const handleMoveDown = (index: number) => {
    reorderWidgets(index, index + 1)
  }

  // Reset Grid to original default configuration
  const handleResetLayout = () => {
    setOrder([...defaultOrder])
    setDraggedId(null)
    setDragOverId(null)
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Grid Toolbar with In-Memory Reset Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1 py-1">
        <div className="flex items-center gap-2 text-xs font-mono text-[#475467]">
          <Sliders className="w-3.5 h-3.5 text-[#244DE8]" />
          <span>ACTIVE DASHBOARD COCKPIT ({currentOrder.length} MODULAR WIDGETS)</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-[#667085] hidden md:inline">
            Use drag handle or arrow controls to rearrange
          </span>
          <Button
            size="xs"
            variant="outline"
            onClick={handleResetLayout}
            icon={<RotateCcw className="w-3 h-3" />}
            title="Restore default widget layout"
            aria-label="Reset Grid Layout"
          >
            Reset Grid
          </Button>
        </div>
      </div>

      {/* Responsive Draggable Grid Container */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {currentOrder.map((id, index) => {
          const widget = widgetMap.get(id)
          if (!widget) return null

          const isBeingDragged = draggedId === id
          const isDragOver = dragOverId === id

          return (
            <div
              key={widget.id}
              role="region"
              aria-label={widget.ariaLabel || widget.title}
              onDragOver={(e) => handleDragOver(e, id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, id)}
              className={cn(
                'relative transition-all duration-200 motion-reduce:transition-none',
                widget.colSpan || 'col-span-1',
                isBeingDragged && 'opacity-40 scale-[0.98]',
                isDragOver && 'ring-2 ring-[#244DE8] ring-offset-2 ring-offset-[#F5F7FB] rounded-xl'
              )}
            >
              <Card className="h-full flex flex-col border border-[#DCE2ED] bg-white hover:border-[#CBD5E1] shadow-xs">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3.5 border-b border-[#EAEFF7]">
                  {/* Left: Drag Handle + Icon + Title */}
                  <div className="flex items-center gap-2 min-w-0">
                    {/* Dedicated Accessible Drag Handle */}
                    <button
                      type="button"
                      draggable
                      onDragStart={(e) => handleDragStart(e, id)}
                      onDragEnd={handleDragEnd}
                      className="cursor-grab active:cursor-grabbing p-1 -ml-1 rounded text-[#667085] hover:text-[#244DE8] hover:bg-[#F1F5F9] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8]"
                      title="Drag to rearrange widget"
                      aria-label={`Drag ${widget.title} to rearrange`}
                    >
                      <GripVertical className="w-4 h-4 shrink-0" />
                    </button>

                    <div className="p-1 rounded-lg bg-[#E8EEFF] text-[#244DE8] shrink-0">
                      {widget.icon}
                    </div>

                    <CardTitle className="text-xs font-semibold font-mono tracking-tight text-[#101828] truncate">
                      {widget.title}
                    </CardTitle>
                  </div>

                  {/* Right: Explicit Keyboard Reorder Controls */}
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleMoveUp(index)}
                      disabled={index === 0}
                      className="p-1 rounded text-[#667085] hover:text-[#101828] hover:bg-[#F1F5F9] disabled:opacity-30 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] transition-colors"
                      title="Move widget up"
                      aria-label={`Move ${widget.title} up`}
                    >
                      <ArrowUp className="w-3.5 h-3.5" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleMoveDown(index)}
                      disabled={index === currentOrder.length - 1}
                      className="p-1 rounded text-[#667085] hover:text-[#101828] hover:bg-[#F1F5F9] disabled:opacity-30 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#244DE8] transition-colors"
                      title="Move widget down"
                      aria-label={`Move ${widget.title} down`}
                    >
                      <ArrowDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </CardHeader>

                {/* Widget Component Content (Fresh live props) */}
                <CardContent className="p-4 flex-1">
                  {widget.component}
                </CardContent>
              </Card>
            </div>
          )
        })}
      </div>
    </div>
  )
}
