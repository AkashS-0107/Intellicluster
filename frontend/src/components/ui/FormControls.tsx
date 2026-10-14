import React from 'react'
import { cn } from '@/utils/cn'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  isMono?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, isMono = false, id, required, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold text-[#344054]">
            {label}
            {required && <span className="text-[#D92D20] ml-1">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          required={required}
          className={cn(
            'flex h-9 w-full rounded-lg border border-[#DCE2ED] bg-white px-3 py-1 text-sm text-[#101828] placeholder:text-[#98A2B3] transition-colors focus-visible:outline-none focus-visible:border-[#244DE8] focus-visible:ring-1 focus-visible:ring-[#244DE8] disabled:cursor-not-allowed disabled:opacity-50 shadow-xs',
            isMono && 'font-mono text-xs',
            error && 'border-[#FDA29B] focus-visible:border-[#D92D20] focus-visible:ring-[#D92D20]',
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-[#D92D20] font-mono">{error}</p>}
        {helperText && !error && <p className="text-[11px] text-[#667085]">{helperText}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  helperText?: string
  isMono?: boolean
  options?: Array<{ label: string; value: string | number }>
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, isMono = false, id, required, options, children, ...props }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-semibold text-[#344054]">
            {label}
            {required && <span className="text-[#D92D20] ml-1">*</span>}
          </label>
        )}
        <select
          id={selectId}
          ref={ref}
          required={required}
          className={cn(
            'flex h-9 w-full rounded-lg border border-[#DCE2ED] bg-white px-3 py-1 text-sm text-[#101828] transition-colors focus-visible:outline-none focus-visible:border-[#244DE8] focus-visible:ring-1 focus-visible:ring-[#244DE8] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer shadow-xs',
            isMono && 'font-mono text-xs',
            error && 'border-[#FDA29B] focus-visible:border-[#D92D20] focus-visible:ring-[#D92D20]',
            className
          )}
          {...props}
        >
          {options
            ? options.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-white text-[#101828]">
                  {opt.label}
                </option>
              ))
            : children}
        </select>
        {error && <p className="text-[11px] text-[#D92D20] font-mono">{error}</p>}
        {helperText && !error && <p className="text-[11px] text-[#667085]">{helperText}</p>}
      </div>
    )
  }
)
Select.displayName = 'Select'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, error, helperText, id, required, ...props }, ref) => {
    const textareaId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined)

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-semibold text-[#344054]">
            {label}
            {required && <span className="text-[#D92D20] ml-1">*</span>}
          </label>
        )}
        <textarea
          id={textareaId}
          ref={ref}
          required={required}
          className={cn(
            'flex min-h-[70px] w-full rounded-lg border border-[#DCE2ED] bg-white px-3 py-2 text-sm text-[#101828] placeholder:text-[#98A2B3] transition-colors focus-visible:outline-none focus-visible:border-[#244DE8] focus-visible:ring-1 focus-visible:ring-[#244DE8] disabled:cursor-not-allowed disabled:opacity-50 shadow-xs',
            error && 'border-[#FDA29B] focus-visible:border-[#D92D20] focus-visible:ring-[#D92D20]',
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-[#D92D20] font-mono">{error}</p>}
        {helperText && !error && <p className="text-[11px] text-[#667085]">{helperText}</p>}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'
