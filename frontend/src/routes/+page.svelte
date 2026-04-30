<script lang="ts">
  import { onMount } from 'svelte';

  let isFinding = $state(false);
  let resultsFound = $state(false);
  let videoElement: HTMLVideoElement | undefined = $state();
  let capturedImage: string | undefined = $state();
  
  let actors = $state<any[]>([]);
  let cartoons = $state<any[]>([]);
  let selectedMatch = $state<any>(null);
  let showOnTV = $state(false);

  onMount(() => {
    startWebcam();
  });

  async function startWebcam() {
    capturedImage = undefined;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 }, 
        audio: false 
      });
      if (videoElement) {
        videoElement.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing webcam:", err);
    }
  }

  async function handleFind() {
    if (!videoElement) return;

    // Capture the current frame to a canvas
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
      capturedImage = canvas.toDataURL('image/jpeg');
    }

    isFinding = true;
    resultsFound = false;

    try {
      const response = await fetch(capturedImage!);
      const blob = await response.blob();
      const formData = new FormData();
      formData.append('file', blob, 'capture.jpg');

      const apiRes = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData
      });

      const data = await apiRes.json();

      if (data.results && data.results.length > 0) {
        const topFace = data.results[0];
        actors = topFace.matches.slice(0, 5).map((m: any) => ({
          name: m.name,
          confidence: m.confidence
        }));
        
        cartoons = topFace.matches.slice(0, 5).map((m: any) => ({
          name: m.name + " (C)",
          confidence: m.confidence * 0.95
        }));
        
        selectedMatch = actors[0];
        showOnTV = false;
        resultsFound = true;
      }
    } catch (err) {
      console.error("Backend Error:", err);
      alert("Backend connection failed!");
    } finally {
      isFinding = false;
    }
  }

  function handleReset() {
    capturedImage = undefined;
    resultsFound = false;
    isFinding = false;
    actors = [];
    cartoons = [];
    selectedMatch = null;
    showOnTV = false;
  }
</script>

<svelte:head>
  <title>Celeb Look-a-like Cam</title>
</svelte:head>

<div class="app-container">
  <!-- Header -->
  <header class="header">
    <h1>Celeb Look-a-like Cam</h1>
  </header>

  <main class="main-layout">
    <!-- Left Column: Stacked Rectangles -->
    <div class="left-column">
      <div class="camera-box">
        <div class="status-indicator" style="position: absolute; top: 12px; left: 12px; z-index: 10;">
          <div class="status-dot"></div>
          LIVE FEED
        </div>
        <!-- svelte-ignore a11y_media_has_caption -->
        <video 
          bind:this={videoElement} 
          autoplay 
          playsinline 
          class="webcam-video"
          style:display={capturedImage ? 'none' : 'block'}
        ></video>
        {#if capturedImage}
          <img src={capturedImage} alt="Captured frame" class="webcam-video" />
        {/if}
      </div>

      <div class="tv-box">
        <div class="status-indicator" style="position: absolute; top: 12px; left: 12px; z-index: 10;">
          <div class="status-dot" style="background: var(--cartoon-accent)"></div>
          TV SCREEN
        </div>
        {#if isFinding}
          <div class="scanning-animation">
            <p style="font-size: 0.7rem; letter-spacing: 2px;">NEURAL SCAN...</p>
            <div class="scan-bar"></div>
          </div>
        {:else if showOnTV && selectedMatch}
          <div class="match-reveal">
            <div class="match-display">
              <div class="match-avatar" style="width: 100px; height: 100px; border: 1px solid var(--cartoon-accent)"></div>
              <h3 style="font-size: 1.1rem; margin: 8px 0;">{selectedMatch.name}</h3>
              <p style="font-size: 0.7rem; color: var(--cartoon-accent); letter-spacing: 1px;">LIVE MATCH PROJECTION</p>
            </div>
          </div>
        {:else if resultsFound && !showOnTV}
          <div class="idle-message">
            <p style="font-size: 0.7rem; letter-spacing: 2px;">MATCHES LOADED</p>
            <p style="font-size: 0.5rem; opacity: 0.5">SELECT A MATCH AND CLICK "SHOW LIVE"</p>
          </div>
        {:else}
          <div class="idle-message">
            <p style="font-size: 0.6rem; letter-spacing: 3px; opacity: 0.2">WAITING FOR INPUT</p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Right Column -->
    <div class="right-column">
      <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 5px;">
        {#if capturedImage}
          <button class="reset-btn" onclick={handleReset}>RESET CAM</button>
        {/if}
        <button class="find-button" onclick={handleFind} disabled={isFinding}>
          {isFinding ? 'ANALYZING...' : 'FIND MATCHES'}
        </button>
      </div>

      <div class="results-grid">
        {#if !resultsFound && !isFinding}
          <!-- Idle Skeletons (No animation) -->
          {#each Array(10) as _}
            <div class="result-block skeleton">
              <div class="result-avatar" style="background: rgba(255, 255, 255, 0.02)"></div>
            </div>
          {/each}
        {:else if isFinding}
           <!-- Loading skeletons (Shimmering) -->
           {#each Array(10) as _}
            <div class="result-block skeleton shimmer">
              <div class="result-avatar" style="background: transparent"></div>
            </div>
          {/each}
        {:else}
          <!-- Real results -->
          {#each actors as actor}
            <button 
              class="result-block actor" 
              class:selected={selectedMatch === actor}
              onclick={() => { selectedMatch = actor; showOnTV = false; }}
            >
              <div class="result-avatar"></div>
              <div class="result-name">{actor.name}</div>
              <div style="font-size: 0.6rem; opacity: 0.5">{Math.round(actor.confidence * 100)}% Match</div>
            </button>
          {/each}

          {#each cartoons as cartoon}
            <button 
              class="result-block cartoon" 
              class:selected={selectedMatch === cartoon}
              onclick={() => { selectedMatch = cartoon; showOnTV = false; }}
            >
              <div class="result-avatar" style="border: 1px solid rgba(0, 255, 136, 0.2)"></div>
              <div class="result-name">{cartoon.name}</div>
              <div style="font-size: 0.6rem; opacity: 0.5">{Math.round(cartoon.confidence * 100)}% Look</div>
            </button>
          {/each}
        {/if}
      </div>

      <!-- Settings Panel -->
      <div class="result-block settings-panel" style="align-items: stretch; border-color: var(--glass-border);">
        <div class="box-title" style="color: #fff; font-size: 0.75rem; margin-bottom: 12px; font-weight: 800;">
          <span>SETTINGS</span>
        </div>
        <div class="settings-content" style="display: flex; flex-direction: column; gap: 10px;">
          <div style="font-size: 0.7rem; opacity: 0.8">
            Selected: <span style="color: var(--cartoon-accent)">{selectedMatch ? selectedMatch.name : 'None'}</span>
          </div>
          <button 
            class="find-button" 
            style="background: var(--cartoon-accent); color: #000; margin-top: auto; width: 100%;"
            onclick={() => showOnTV = true}
            disabled={!selectedMatch}
          >
            SHOW LIVE
          </button>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .scanning-animation {
    text-align: center;
  }
  
  .scan-bar {
    width: 120px;
    height: 1px;
    background: var(--cartoon-accent);
    margin: 12px auto;
    position: relative;
    overflow: hidden;
  }
  
  .scan-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, white, transparent);
    animation: scan 1s infinite;
  }
  
  @keyframes scan {
    from { left: -100%; }
    to { left: 100%; }
  }

  .match-reveal {
    text-align: center;
    animation: fadeIn 0.4s ease-out;
  }

  .match-display {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .match-avatar {
    background: #111;
    border-radius: 6px;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: scale(0.98); }
    to { opacity: 1; transform: scale(1); }
  }

  .idle-message {
    text-align: center;
  }
</style>
