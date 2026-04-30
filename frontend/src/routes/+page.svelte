<script lang="ts">
  import { onMount } from 'svelte';
  import VideoPanel from '$lib/components/VideoPanel.svelte';
  import ResultCard from '$lib/components/ResultCard.svelte';
  import AppButton from '$lib/components/AppButton.svelte';

  let isFinding = $state(false);
  let resultsFound = $state(false);
  let videoElement: HTMLVideoElement | undefined = $state();
  let tvVideoElement: HTMLVideoElement | undefined = $state();
  let capturedImage: string | undefined = $state();
  
  let actors = $state<any[]>([]);
  let cartoons = $state<any[]>([]);
  let selectedMatch = $state<any>(null);
  let showOnTV = $state(false);
  let projectionStep = $state(0); // 0: Idle, 1 or 2 for steps

  let stream: MediaStream | undefined = $state();

  onMount(() => {
    startWebcam();
  });

  $effect(() => {
    if (stream && tvVideoElement && !tvVideoElement.srcObject) {
      tvVideoElement.srcObject = stream;
    }
  });

  async function startWebcam() {
    capturedImage = undefined;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 }, 
        audio: false 
      });
      if (videoElement) videoElement.srcObject = stream;
    } catch (err) {
      console.error("Error accessing webcam:", err);
    }
  }

  async function handleFind() {
    if (!videoElement) return;

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
        actors = topFace.matches.slice(0, 5).map((m: any) => ({ name: m.name, confidence: m.confidence }));
        cartoons = topFace.matches.slice(0, 5).map((m: any) => ({ name: m.name + " (C)", confidence: m.confidence * 0.95 }));
        selectedMatch = actors[0];
        resultsFound = true;
      }
    } catch (err) {
      console.error("Backend Error:", err);
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
    projectionStep = 0;
  }

  function startProjection() {
    if (!selectedMatch) return;
    showOnTV = true;
    projectionStep = 1;
    
    // Switch to comparison after 2.5 seconds
    setTimeout(() => {
      if (showOnTV) projectionStep = 2;
    }, 2500);
  }
</script>

<div class="app-container">
  <header class="header">
    <h1>Celeb Look-a-like Cam</h1>
  </header>

  <main class="main-layout">
    <div class="left-column">
      <VideoPanel title="Live Feed" accent="#00ff88">
        <!-- svelte-ignore a11y_media_has_caption -->
        <video bind:this={videoElement} autoplay playsinline class="webcam-video"></video>
        {#if capturedImage}
          <div class="capture-thumbnail">
            <img src={capturedImage} alt="Capture" />
          </div>
        {/if}
      </VideoPanel>

      <VideoPanel title="TV Screen" accent="#00ff88">
        {#if isFinding}
          <div class="scanning-indicator">
            <span class="scan-text">SCANNING FACIAL GEOMETRY...</span>
            <div class="scan-bar"></div>
          </div>
        {:else if showOnTV && selectedMatch}
          <div class="tv-projection-container step-{projectionStep}">
            <!-- Live Feed Side -->
            <div class="projection-part live-side">
              <div class="avatar-medium">
                <!-- svelte-ignore a11y_media_has_caption -->
                <video bind:this={tvVideoElement} autoplay playsinline class="webcam-video"></video>
              </div>
            </div>
            
            <!-- Arrow -->
            <div class="projection-part arrow-side">
              <div class="big-arrow">&gt;</div>
            </div>

            <!-- Match Side -->
            <div class="projection-part match-side">
              <div class={projectionStep === 1 ? 'avatar-large' : 'avatar-medium'}>
                <!-- Match image will go here -->
              </div>
            </div>
          </div>
        {:else}
          <div class="idle-message">
            <p style="font-size: 0.6rem; letter-spacing: 3px; opacity: 0.2">
              {resultsFound ? 'SELECT A MATCH' : 'WAITING FOR INPUT'}
            </p>
          </div>
        {/if}
      </VideoPanel>
    </div>

    <div class="right-column">
      <div class="controls-row">
        {#if capturedImage}
          <AppButton variant="secondary" onclick={handleReset}>Reset Cam</AppButton>
        {/if}
        <AppButton variant="primary" onclick={handleFind} disabled={isFinding} style="min-width: 180px;">
          {isFinding ? 'Analyzing...' : 'Find Matches'}
        </AppButton>
      </div>

      <div class="results-grid">
        {#if !resultsFound && !isFinding}
          {#each Array(10) as _}
            <ResultCard type="skeleton" />
          {/each}
        {:else if isFinding}
          {#each Array(10) as _}
            <ResultCard type="skeleton" shimmer />
          {/each}
        {:else}
          {#each actors as actor}
            <ResultCard 
              item={actor} 
              type="actor" 
              selected={selectedMatch === actor} 
              onclick={() => { selectedMatch = actor; showOnTV = false; projectionStep = 0; }} 
            />
          {/each}
          {#each cartoons as cartoon}
            <ResultCard 
              item={cartoon} 
              type="cartoon" 
              selected={selectedMatch === cartoon} 
              onclick={() => { selectedMatch = cartoon; showOnTV = false; projectionStep = 0; }} 
            />
          {/each}
        {/if}
      </div>

      <div class="settings-card">
        <div class="card-header">SETTINGS</div>
        <div class="card-body">
          <div class="selection-status">
            Selected: <span>{selectedMatch ? selectedMatch.name : 'None'}</span>
          </div>
          <AppButton 
            variant="primary" 
            onclick={startProjection} 
            disabled={!selectedMatch}
            style="width: 100%; background: var(--accent-color); color: #000;"
          >
            Show Live
          </AppButton>
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  .controls-row {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    align-items: center;
  }

  .settings-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
  }

  .card-header {
    font-size: 0.75rem;
    font-weight: 900;
    letter-spacing: 2px;
    opacity: 0.5;
  }

  .selection-status {
    font-size: 0.8rem;
    opacity: 0.8;
  }

  .selection-status span {
    color: var(--accent-color);
    font-weight: 700;
  }

  .scanning-indicator {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }

  .scan-text {
    font-size: 0.7rem;
    letter-spacing: 2px;
    font-weight: 700;
  }

  .scan-bar {
    width: 140px;
    height: 2px;
    background: var(--accent-color);
    position: relative;
    overflow: hidden;
  }

  .scan-bar::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, #fff, transparent);
    animation: scan 1.5s infinite;
  }

  @keyframes scan {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .label {
    font-size: 0.55rem;
    margin-top: 10px;
    opacity: 0.4;
    letter-spacing: 1px;
    font-weight: 700;
  }

  .name-tag {
    font-size: 0.9rem;
    font-weight: 800;
    margin-top: 10px;
    color: #fff;
    transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .name-tag-large {
    font-size: 1.8rem;
    font-weight: 900;
    margin-top: 15px;
    color: #fff;
    transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .idle-message {
    text-align: center;
  }
</style>
