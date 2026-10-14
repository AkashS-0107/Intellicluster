import React, { useEffect } from 'react'
import { cn } from '@/utils/cn'
import { X } from 'lucide-react'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: React.ReactNode
  description?: React.ReactNode
  children: React.ReactNode
  footer?: React.ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  maxWidth = 'md',
}: ModalProps) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.body.style.overflow = 'unset'
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const widthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          'relative w-full rounded-xl border border-[#DCE2ED] bg-white p-6 text-[#101828] shadow-2xl z-10 animate-in fade-in zoom-in-95 duration-150',
          widthClasses[maxWidth]
        )}
      >
        <div className="flex items-start justify-between border-b border-[#EAEFF7] pb-3">
          <div>
            <h3 className="text-base font-semibold tracking-tight text-[#101828]">{title}</h3>
            {description && <p className="mt-1 text-xs text-[#667085]">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[#667085] hover:bg-[#F1F5F9] hover:text-[#101828] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]"
            aria-label="Close dialog"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="mt-4">{children}</div>

        {footer && (
          <div className="mt-6 flex items-center justify-end gap-2 border-t border-[#EAEFF7] pt-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}

export interface DrawerProps {
  isOpen: boolean
  onClose: () => void
  title: React.ReactNode
  description?: React.ReactNode
  children: React.ReactNode
  footer?: React.ReactNode
  width?: string
}

export function Drawer({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  width = 'max-w-lg',
}: DrawerProps) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.body.style.overflow = 'unset'
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="fixed inset-y-0 right-0 flex pl-10">
        <div
          role="dialog"
          aria-modal="true"
          className={cn(
            'w-screen border-l border-[#DCE2ED] bg-white p-6 shadow-2xl flex flex-col text-[#101828]',
            width
          )}
        >
          <div className="flex items-start justify-between border-b border-[#EAEFF7] pb-4">
            <div>
              <h3 className="text-base font-semibold tracking-tight text-[#101828]">{title}</h3>
              {description && <p className="mt-1 text-xs text-[#667085]">{description}</p>}
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-[#667085] hover:bg-[#F1F5F9] hover:text-[#101828] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8]"
              aria-label="Close drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto py-4">{children}</div>

          {footer && (
            <div className="border-t border-[#EAEFF7] pt-4 flex items-center justify-end gap-2">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
