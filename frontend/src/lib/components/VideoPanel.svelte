<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    accent?: string;
    children: Snippet;
  }

  let { title, accent = '#fff', children }: Props = $props();
</script>

<div class="panel">
  <div class="status-bar">
    <div class="dot" style="background: {accent}"></div>
    <span class="title">{title}</span>
  </div>
  <div class="content">
    {@render children()}
  </div>
</div>

<style>
  .panel {
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .status-bar {
    position: absolute;
    top: 15px;
    left: 15px;
    z-index: 10;
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(0, 0, 0, 0.4);
    padding: 4px 10px;
    border-radius: 4px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    box-shadow: 0 0 8px currentColor;
    animation: blink 2s infinite;
  }

  .title {
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 1px;
    color: #fff;
    text-transform: uppercase;
    opacity: 0.8;
  }

  .content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
</style>
