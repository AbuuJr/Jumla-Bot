import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

// ============================================================================
// Card Component - Container with optional header and footer
// ============================================================================

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, padding = 'md', shadow = 'sm', ...props }, ref) => {
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const shadowClasses = {
      none: '',
      sm: 'shadow-sm',
      md: 'shadow-md',
      lg: 'shadow-lg',
    };

    return (
      <div
        ref={ref}
        className={clsx(
          'rounded-lg border border-neutral-200 bg-white',
          paddingClasses[padding],
          shadowClasses[shadow],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// ===== Card Sub-components =====
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, children, className, ...props }, ref) => (
    <div ref={ref} className={clsx('mb-4', className)} {...props}>
      {title && <h3 className="text-lg font-semibold text-neutral-900">{title}</h3>}
      {subtitle && <p className="mt-1 text-sm text-neutral-500">{subtitle}</p>}
      {children}
    </div>
  )
);

CardHeader.displayName = 'CardHeader';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx('mt-4 flex items-center justify-end gap-3 border-t border-neutral-200 pt-4', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';

export default Card;