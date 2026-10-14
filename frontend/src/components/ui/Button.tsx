import React from 'react'
import { cn } from '@/utils/cn'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  isLoading?: boolean
  icon?: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'secondary',
      size = 'md',
      isLoading = false,
      disabled,
      icon,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#244DE8] focus-visible:ring-offset-1 disabled:pointer-events-none disabled:opacity-50 select-none active:scale-[0.98]'

    const sizeStyles = {
      xs: 'h-7 px-2.5 text-xs rounded-md gap-1.5',
      sm: 'h-8 px-3 text-xs rounded-md gap-1.5',
      md: 'h-9 px-4 text-sm rounded-lg gap-2',
      lg: 'h-10 px-5 text-sm rounded-lg gap-2.5',
    }

    const variantStyles = {
      primary:
        'bg-[#244DE8] text-white hover:bg-[#1D40C7] active:bg-[#16329C] font-semibold shadow-sm border border-[#1D40C7]',
      secondary:
        'bg-white text-[#101828] border border-[#DCE2ED] hover:bg-[#F8FAFC] hover:border-[#CBD5E1] shadow-xs active:bg-[#F1F5F9]',
      danger:
        'bg-[#FEF3F2] text-[#B42318] border border-[#FECDCA] hover:bg-[#FEE4E2] active:bg-[#FECDCA] font-medium',
      ghost:
        'text-[#475467] hover:text-[#101828] hover:bg-[#F1F5F9]',
      outline:
        'border border-[#DCE2ED] bg-white text-[#344054] hover:bg-[#F8FAFC] hover:border-[#CBD5E1] shadow-xs',
    }

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          icon && <span className="shrink-0">{icon}</span>
        )}
        <span>{children}</span>
      </button>
    )
  }
)

Button.displayName = 'Button'
