// frontend/src/components/ui/Button.jsx
import React from 'react'
import { Loader2 } from 'lucide-react'

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  className = '',
  icon: Icon,
  ...props
}) {
  const baseClasses =
    'inline-flex items-center justify-center font-semibold rounded-lg transition-colors duration-300 focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-black focus-visible:ring-status-info disabled:opacity-40 disabled:cursor-not-allowed select-none'

  const sizeClasses = {
    xsm: 'px-2.5 py-1 button-xsm gap-1',
    sm:  'px-3 py-1.5 button-sm gap-1.5',
    md:  'px-5 py-2.5 button-md gap-2',
    lg:  'px-6 py-3 button-lg gap-2.5',
  }[size] || 'px-5 py-2.5 button-md gap-2'

  const variantClasses = {
    primary:
      'bg-white text-black hover:bg-neutral-200 active:bg-neutral-300 border border-transparent',
    secondary:
      'bg-bg-raised text-white border border-border-default hover:bg-neutral-800 active:bg-neutral-900',
    ghost:
      'bg-transparent text-text-secondary hover:text-white hover:bg-bg-raised active:bg-bg-card',
    danger:
      'bg-status-critical/15 text-status-critical border border-status-critical/30 hover:bg-status-critical/25 active:bg-status-critical/35',
  }[variant] || 'bg-white text-black hover:bg-neutral-200'

  return (
    <button
      disabled={disabled || isLoading}
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`}
      {...props}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
          <span>Processing</span>
        </>
      ) : (
        <>
          {Icon && <Icon className="w-4 h-4" aria-hidden="true" />}
          {children}
        </>
      )}
    </button>
  )
}

