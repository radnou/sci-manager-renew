<script lang="ts">
  type Variant = 'info' | 'success' | 'warning' | 'error' | 'neutral';
  type Size = 'sm' | 'md';

  interface Props {
    text: string;
    variant?: Variant;
    size?: Size;
  }

  let { text, variant = 'neutral', size = 'sm' }: Props = $props();

  const variantClasses: Record<Variant, string> = {
    info: 'bg-ds-info-soft text-ds-info',
    success: 'bg-ds-success-soft text-ds-success',
    warning: 'bg-ds-warning-soft text-ds-warning',
    error: 'bg-ds-error-soft text-ds-error',
    neutral: 'bg-secondary text-secondary-foreground'
  };

  const sizeClasses: Record<Size, string> = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-[11px]'
  };
</script>

<span class="inline-flex items-center rounded-full font-semibold uppercase tracking-wider {variantClasses[variant]} {sizeClasses[size]}">
  {text}
</span>
