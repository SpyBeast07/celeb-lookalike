<script lang="ts">
  interface Props {
    item?: { name: string; confidence: number };
    type?: 'actor' | 'cartoon' | 'skeleton';
    selected?: boolean;
    shimmer?: boolean;
    onclick?: () => void;
  }

  let { item, type = 'actor', selected = false, shimmer = false, onclick }: Props = $props();
</script>

<button 
  class="result-card {type}" 
  class:selected 
  class:skeleton={type === 'skeleton'}
  class:shimmer={type === 'skeleton' && shimmer}
  {onclick}
  disabled={type === 'skeleton'}
>
  <div class="avatar-box">
    {#if type !== 'skeleton'}
      <div class="avatar-placeholder"></div>
    {/if}
  </div>
  
  {#if type !== 'skeleton' && item}
    <div class="info">
      <span class="name">{item.name}</span>
      <span class="meta">{Math.round(item.confidence * 100)}% {type === 'actor' ? 'Match' : 'Look'}</span>
    </div>
  {/if}
</button>

<style>
  .result-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    width: 100%;
    aspect-ratio: 1 / 1.1;
  }

  .result-card:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }

  .result-card.selected {
    background: rgba(0, 255, 136, 0.05);
    border-color: #00ff88;
    box-shadow: 0 0 20px rgba(0, 255, 136, 0.15);
  }

  .avatar-box {
    width: 80%;
    aspect-ratio: 1/1;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 6px;
    margin-bottom: 10px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .name {
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }

  .meta {
    font-size: 0.6rem;
    color: rgba(255, 255, 255, 0.4);
    font-weight: 500;
  }

  /* Skeleton State */
  .skeleton {
    cursor: default;
    opacity: 0.4;
  }

  .shimmer::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0; left: 0;
    transform: translateX(-100%);
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    100% { transform: translateX(100%); }
  }
</style>
