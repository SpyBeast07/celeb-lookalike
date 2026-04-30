<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'danger';
    onclick?: () => void;
    disabled?: boolean;
    children: Snippet;
    style?: string;
  }

  let { variant = 'primary', onclick, disabled = false, children, style }: Props = $props();
</script>

<button 
  class="btn {variant}" 
  {onclick} 
  {disabled}
  {style}
>
  {@render children()}
</button>

<style>
  .btn {
    border: none;
    padding: 10px 24px;
    font-size: 0.75rem;
    font-weight: 800;
    border-radius: 6px;
    cursor: pointer;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    white-space: nowrap;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    filter: grayscale(1);
  }

  .primary {
    background: #fff;
    color: #000;
  }

  .primary:hover:not(:disabled) {
    background: #eee;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
  }

  .secondary {
    background: rgba(255, 255, 255, 0.05);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.2);
  }

  .danger {
    background: rgba(255, 68, 68, 0.1);
    color: #ff4444;
    border: 1px solid rgba(255, 68, 68, 0.2);
  }

  .danger:hover:not(:disabled) {
    background: rgba(255, 68, 68, 0.2);
    border-color: #ff4444;
  }
</style>
