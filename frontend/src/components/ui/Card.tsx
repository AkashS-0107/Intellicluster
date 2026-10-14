import React from 'react'
import { cn } from '@/utils/cn'

export function Card({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-xl border border-[#DCE2ED] bg-white text-[#101828] shadow-sm',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex flex-col space-y-1 p-4 sm:p-5 border-b border-[#EAEFF7]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        'text-sm font-semibold tracking-tight text-[#101828] flex items-center justify-between',
        className
      )}
      {...props}
    >
      {children}
    </h3>
  )
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn('text-xs text-[#667085]', className)}
      {...props}
    >
      {children}
    </p>
  )
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('p-4 sm:p-5', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex items-center p-4 sm:p-5 pt-0 border-t border-[#EAEFF7] mt-4',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export interface MetricCardProps {
  label: string
  value: React.ReactNode
  subtext?: React.ReactNode
  icon?: React.ReactNode
  variant?: 'default' | 'cyan' | 'success' | 'warning' | 'critical'
  className?: string
}

export function MetricCard({
  label,
  value,
  subtext,
  icon,
  variant = 'default',
  className,
}: MetricCardProps) {
  const accentBorder = {
    default: 'border-[#DCE2ED] hover:border-[#CBD5E1]',
    cyan: 'border-[#DCE2ED] hover:border-[#244DE8]/60',
    success: 'border-[#DCE2ED] hover:border-[#12B76A]/60',
    warning: 'border-[#DCE2ED] hover:border-[#F79009]/60',
    critical: 'border-[#DCE2ED] hover:border-[#D92D20]/60',
  }

  const iconColors = {
    default: 'bg-[#F1F5F9] text-[#475467]',
    cyan: 'bg-[#E8EEFF] text-[#244DE8]',
    success: 'bg-[#ECFDF3] text-[#027A48]',
    warning: 'bg-[#FFFAEB] text-[#B54708]',
    critical: 'bg-[#FEF3F2] text-[#B42318]',
  }

  return (
    <div
      className={cn(
        'rounded-xl border bg-white p-4 sm:p-5 transition-all shadow-sm hover:shadow-md relative overflow-hidden',
        accentBorder[variant],
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[#667085] uppercase tracking-wider font-mono">
          {label}
        </span>
        {icon && <div className={cn('p-1.5 rounded-lg shrink-0', iconColors[variant])}>{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline">
        <span className="text-2xl font-bold font-mono tracking-tight text-[#101828] tabular-nums">
          {value}
        </span>
      </div>
      {subtext && (
        <div className="mt-1.5 text-xs text-[#667085] flex items-center gap-1 font-sans">
          {subtext}
        </div>
      )}
    </div>
  )
}
