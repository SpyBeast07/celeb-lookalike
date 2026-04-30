<script lang="ts">
  import { onMount } from 'svelte';

  let isFinding = $state(false);
  let resultsFound = $state(false);
  let videoElement: HTMLVideoElement | undefined = $state();
  let capturedImage: string | undefined = $state();

  onMount(() => {
    startWebcam();
  });

  async function startWebcam() {
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

  const actors = [
    { name: 'Brad Pitt', confidence: 0.95 },
    { name: 'Tom Cruise', confidence: 0.88 },
    { name: 'Johnny Depp', confidence: 0.82 },
    { name: 'Leonardo DiCaprio', confidence: 0.75 },
    { name: 'Robert Downey Jr.', confidence: 0.68 }
  ];

  const cartoons = [
    { name: 'Sherlock Holmes', confidence: 0.92 },
    { name: 'Batman', confidence: 0.85 },
    { name: 'Spider-Man', confidence: 0.78 },
    { name: 'Iron Man', confidence: 0.70 },
    { name: 'Jack Sparrow', confidence: 0.65 }
  ];

  function handleFind() {
    if (!videoElement) return;

    // Capture the current frame to a canvas
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const ctx = canvas.getContext('2d');
    if (ctx) {
      // Draw raw frame; the .webcam-video CSS class will handle mirroring 
      // the display for the user, matching the live preview.
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
      
      // Get base64 image
      capturedImage = canvas.toDataURL('image/jpeg');
    }

    isFinding = true;
    resultsFound = false;
    
    // Simulate finding process
    setTimeout(() => {
      isFinding = false;
      resultsFound = true;
    }, 2000);
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
          <button 
            onclick={() => capturedImage = undefined}
            class="reset-btn"
          >
            RESET
          </button>
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
        {:else if resultsFound}
          <div class="match-reveal">
            <div class="match-display">
              <div class="match-avatar" style="width: 80px; height: 80px; border: 1px solid var(--cartoon-accent)"></div>
              <h3 style="font-size: 1rem; margin: 8px 0;">{actors[0].name}</h3>
              <p style="font-size: 0.65rem; color: var(--cartoon-accent); letter-spacing: 1px;">OPTIMAL MATCH</p>
            </div>
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
      <!-- Find Button below the divider line -->
      <button class="find-button" onclick={handleFind} disabled={isFinding}>
        {isFinding ? 'ANALYZING...' : 'FIND MATCHES'}
      </button>

      <div class="results-grid">
        {#each actors as actor}
          <div class="result-block actor">
            <div class="result-avatar"></div>
            <div class="result-name">{actor.name}</div>
            <div style="font-size: 0.6rem; opacity: 0.5">{Math.round(actor.confidence * 100)}% Match</div>
          </div>
        {/each}

        {#each cartoons as cartoon}
          <div class="result-block cartoon">
            <div class="result-avatar" style="border: 1px solid rgba(0, 255, 136, 0.2)"></div>
            <div class="result-name">{cartoon.name}</div>
            <div style="font-size: 0.6rem; opacity: 0.5">{Math.round(cartoon.confidence * 100)}% Look</div>
          </div>
        {/each}
      </div>

      <!-- Settings Panel -->
      <div class="result-block settings-panel" style="align-items: stretch; border-color: rgba(255, 68, 68, 0.2);">
        <div class="box-title" style="color: var(--settings-accent); font-size: 0.75rem; margin-bottom: 12px; font-weight: 800;">
          <span>SYSTEM DIAGNOSTICS</span>
          <div class="status-indicator">
            <div class="status-dot"></div>
            ACTIVE
          </div>
        </div>
        <div class="settings-content" style="font-size: 0.75rem; opacity: 0.8">
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>ENGINE</span>
            <span style="color: var(--cartoon-accent)">SPYBEAST_v4.2</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>LATENCY</span>
            <span>18ms</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span>AI CORE</span>
            <span style="color: var(--cartoon-accent)">LOADED</span>
          </div>
          <div style="margin-top: 18px; height: 2px; background: #222; border-radius: 1px; overflow: hidden;">
            <div style="width: 92%; height: 100%; background: var(--settings-accent)"></div>
          </div>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .placeholder-text {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.05);
    font-size: 0.7rem;
    letter-spacing: 5px;
  }

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
