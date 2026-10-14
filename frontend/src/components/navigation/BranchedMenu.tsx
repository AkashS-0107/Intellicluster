import React, { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Cpu,
  Layers,
  Server,
  Activity,
  Brain,
  ChevronDown,
  Terminal,
  Boxes,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/utils/cn'

export interface MenuItem {
  name: string
  path: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

export interface MenuSection {
  id: string
  title: string
  icon: React.ComponentType<{ className?: string }>
  items: MenuItem[]
}

export const MENU_SECTIONS: MenuSection[] = [
  {
    id: 'operations',
    title: 'Operations',
    icon: Terminal,
    items: [
      { name: 'Dashboard', path: '/app', icon: LayoutDashboard },
      { name: 'Workloads', path: '/workloads', icon: Cpu },
    ],
  },
  {
    id: 'infrastructure',
    title: 'Infrastructure',
    icon: Boxes,
    items: [
      { name: 'Clusters', path: '/clusters', icon: Layers },
      { name: 'Nodes', path: '/nodes', icon: Server },
      { name: 'Telemetry', path: '/telemetry', icon: Activity },
    ],
  },
  {
    id: 'intelligence',
    title: 'Intelligence',
    icon: Sparkles,
    items: [
      { name: 'ML Registry', path: '/ml-registry', icon: Brain },
    ],
  },
]

function isItemActive(itemPath: string, currentPath: string): boolean {
  if (itemPath === '/' || itemPath === '/app') {
    return currentPath === itemPath
  }
  return currentPath.startsWith(itemPath)
}

interface BranchedMenuProps {
  isCollapsed?: boolean
  onNavigate?: () => void
  className?: string
}

export function BranchedMenu({
  isCollapsed = false,
  onNavigate,
  className,
}: BranchedMenuProps) {
  const location = useLocation()

  // Track expanded state of sections
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {
      operations: true,
      infrastructure: true,
      intelligence: true,
    }
    return initial
  })

  // Automatically expand section containing active route on route change
  useEffect(() => {
    MENU_SECTIONS.forEach((section) => {
      const containsActive = section.items.some((item) =>
        isItemActive(item.path, location.pathname)
      )
      if (containsActive) {
        setExpandedSections((prev) => ({
          ...prev,
          [section.id]: true,
        }))
      }
    })
  }, [location.pathname])

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }))
  }

  return (
    <nav
      className={cn('space-y-4 select-none', className)}
      aria-label="Primary Navigation"
    >
      {MENU_SECTIONS.map((section) => {
        const SectionIcon = section.icon
        const isExpanded = !!expandedSections[section.id]
        const hasActiveChild = section.items.some((item) =>
          isItemActive(item.path, location.pathname)
        )

        if (isCollapsed) {
          // Compact rail view: show section items directly as icons
          return (
            <div key={section.id} className="space-y-1.5 py-1 border-b border-[#EAEFF7] last:border-b-0">
              {section.items.map((item) => {
                const ItemIcon = item.icon
                const isActive = isItemActive(item.path, location.pathname)

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/' || item.path === '/app'}
                    onClick={onNavigate}
                    className={cn(
                      'group relative flex h-10 w-10 items-center justify-center rounded-lg mx-auto transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]',
                      isActive
                        ? 'bg-[#E8EEFF] text-[#244DE8] border border-[#C7D7FE] shadow-2xs'
                        : 'text-[#667085] hover:bg-[#F8FAFC] hover:text-[#101828]'
                    )}
                    title={item.name}
                    aria-label={item.name}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <ItemIcon className="h-4 w-4 shrink-0 transition-colors" />
                    {isActive && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-[#244DE8] rounded-r" />
                    )}
                  </NavLink>
                )
              })}
            </div>
          )
        }

        return (
          <div key={section.id} className="space-y-1">
            {/* Section Header Accordion Trigger */}
            <button
              type="button"
              onClick={() => toggleSection(section.id)}
              className={cn(
                'group flex w-full items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono tracking-wider uppercase transition-colors',
                hasActiveChild
                  ? 'text-[#244DE8] font-bold bg-[#E8EEFF]/40'
                  : 'text-[#667085] hover:text-[#101828] hover:bg-[#F8FAFC]'
              )}
              aria-expanded={isExpanded}
              aria-controls={`menu-section-${section.id}`}
            >
              <div className="flex items-center gap-2">
                <SectionIcon
                  className={cn(
                    'h-3.5 w-3.5 transition-colors',
                    hasActiveChild ? 'text-[#244DE8]' : 'text-[#98A2B3] group-hover:text-[#475467]'
                  )}
                />
                <span>{section.title}</span>
              </div>
              <ChevronDown
                className={cn(
                  'h-3.5 w-3.5 text-[#98A2B3] transition-transform duration-200',
                  isExpanded ? 'rotate-0' : '-rotate-90'
                )}
              />
            </button>

            {/* Expandable Section Items with SVG Branch Line Connectors */}
            {isExpanded && (
              <div
                id={`menu-section-${section.id}`}
                className="relative pl-3.5 pt-0.5 space-y-0.5"
                role="group"
                aria-label={section.title}
              >
                {/* Continuous Vertical Branch Trunk */}
                <div
                  className="absolute left-[13px] top-1 bottom-3 w-[1.5px] bg-[#DCE2ED] pointer-events-none"
                  aria-hidden="true"
                />

                {section.items.map((item) => {
                  const ItemIcon = item.icon
                  const isActive = isItemActive(item.path, location.pathname)

                  return (
                    <div key={item.path} className="relative flex items-center">
                      {/* SVG Branch Curve connecting trunk to child */}
                      <svg
                        className="absolute left-[-2px] top-1/2 -translate-y-1/2 h-6 w-4 pointer-events-none"
                        viewBox="0 0 16 24"
                        fill="none"
                        aria-hidden="true"
                      >
                        <path
                          d="M 2 0 V 12 C 2 16 6 16 14 16"
                          stroke={isActive ? '#244DE8' : '#DCE2ED'}
                          strokeWidth="1.5"
                          strokeLinecap="round"
                        />
                      </svg>

                      {/* NavLink Item */}
                      <NavLink
                        to={item.path}
                        end={item.path === '/' || item.path === '/app'}
                        onClick={onNavigate}
                        className={({ isActive: linkActive }) =>
                          cn(
                            'group relative ml-3.5 flex flex-1 items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-medium transition-all duration-150',
                            linkActive
                              ? 'bg-[#E8EEFF] text-[#244DE8] border border-[#C7D7FE] shadow-2xs font-semibold'
                              : 'text-[#475467] hover:bg-[#F8FAFC] hover:text-[#101828]'
                          )
                        }
                        aria-current={isActive ? 'page' : undefined}
                      >
                        {({ isActive: linkActive }) => (
                          <>
                            <div className="flex items-center gap-2.5">
                              <ItemIcon
                                className={cn(
                                  'h-3.5 w-3.5 shrink-0 transition-colors',
                                  linkActive
                                    ? 'text-[#244DE8]'
                                    : 'text-[#98A2B3] group-hover:text-[#475467]'
                                )}
                              />
                              <span className="truncate">{item.name}</span>
                            </div>

                            {linkActive && (
                              <span
                                className="h-1.5 w-1.5 rounded-full bg-[#244DE8]"
                                aria-hidden="true"
                              />
                            )}
                          </>
                        )}
                      </NavLink>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}
