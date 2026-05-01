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

	let manualSelectedImage: string | null = $state(null);
	let stream: MediaStream | undefined = $state();

	// Search feature state
	let searchQuery = $state('');
	let isSearching = $state(false);
	let searchResults = $state<any[]>([]);
	let searchMode = $state(false); // true when showing search results instead of AI results

	// Projection state (frozen when "Show Live" is clicked)
	let projectedMatch = $state<any>(null);
	let projectedManualImage = $state<string | null>(null);

	onMount(() => {
		startWebcam();
	});

	$effect(() => {
		if (stream && tvVideoElement && !tvVideoElement.srcObject) {
			tvVideoElement.srcObject = stream;
		}
	});

	// Watch for selection changes to reset manual override
	$effect(() => {
		// Access selectedMatch to subscribe to its changes
		if (selectedMatch) {
			// Logic for selection change
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
			console.error('Error accessing webcam:', err);
		}
	}

	async function fetchCelebImage(name: string, age?: number, type: 'actor' | 'cartoon' = 'actor') {
		try {
			const cleanName = name.replace(' (C)', '').split('_').join(' ');

			if (type === 'actor') {
				// --- ACTOR SEARCH LOGIC ---
				const possibleTitles = [
					`${cleanName} (actor)`,
					`${cleanName} (Indian actor)`,
					cleanName,
					`${cleanName} (Bollywood actor)`,
					`${cleanName} (model)`
				];

				for (const title of possibleTitles) {
					const directUrl = `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(title)}&prop=pageimages&format=json&pithumbsize=600&redirects=1&origin=*`;
					const directRes = await fetch(directUrl);
					const directData = await directRes.json();

					if (directData.query && directData.query.pages) {
						const pages = directData.query.pages;
						const pageId = Object.keys(pages)[0];
						const page: any = pages[pageId];
						if (pageId !== '-1' && page.thumbnail) {
							if (title === cleanName) {
								const lowerTitle = page.title.toLowerCase();
								if (
									lowerTitle.includes('temple') ||
									lowerTitle.includes('statue') ||
									lowerTitle.includes('shrine')
								)
									continue;
							}
							return page.thumbnail.source;
						}
					}
				}

				const queries = [`${cleanName} actor portrait`, `${cleanName} bollywood`, cleanName];

				for (const query of queries) {
					const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(query)}&gsrlimit=10&prop=pageimages&format=json&pithumbsize=600&origin=*`;
					const searchRes = await fetch(searchUrl);
					const searchData = await searchRes.json();

					if (searchData.query && searchData.query.pages) {
						const results = Object.values(searchData.query.pages) as any[];
						const target = cleanName.toLowerCase();
						const firstWord = target.split(' ')[0];

						for (const page of results) {
							const title = page.title.toLowerCase();
							if (title.includes(firstWord)) {
								if (title.includes('actor') || title.includes('bollywood') || title === target) {
									if (page.thumbnail) return page.thumbnail.source;
								}
							}
						}
						const firstWithThumb = results.find(
							(p) => p.thumbnail && p.title.toLowerCase().includes(firstWord)
						);
						if (firstWithThumb) return firstWithThumb.thumbnail.source;
					}
				}
			} else {
				// --- CARTOON SEARCH LOGIC (Robust Reimplementation) ---
				// 1. Try Opensearch first to find the most likely Wikipedia page
				try {
					const opensearchUrl = `https://en.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(cleanName)}&limit=5&format=json&origin=*`;
					const openRes = await fetch(opensearchUrl);
					const openData = await openRes.json();

					if (openData && openData[1] && openData[1].length > 0) {
						for (const title of openData[1]) {
							const lowerTitle = title.toLowerCase();
							// Prioritize titles that clearly indicate a character or animation
							if (
								lowerTitle.includes('character') ||
								lowerTitle.includes('animated') ||
								lowerTitle.includes('cartoon') ||
								lowerTitle.includes('anime') ||
								lowerTitle.includes('series') ||
								lowerTitle === cleanName.toLowerCase()
							) {
								const imgUrl = `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(title)}&prop=pageimages&format=json&pithumbsize=600&redirects=1&origin=*`;
								const imgRes = await fetch(imgUrl);
								const imgData = await imgRes.json();

								if (imgData.query && imgData.query.pages) {
									const pages = imgData.query.pages;
									const pageId = Object.keys(pages)[0];
									const page: any = pages[pageId];
									if (pageId !== '-1' && page.thumbnail) {
										return page.thumbnail.source;
									}
								}
							}
						}
					}
				} catch (e) {
					console.warn('Opensearch failed for cartoon, falling back...', e);
				}

				// 2. Fallback to Direct Disambiguation Titles
				const possibleTitles = [
					`${cleanName} (character)`,
					`${cleanName} (animated character)`,
					`${cleanName} (Disney character)`,
					`${cleanName} (Pixar character)`,
					`${cleanName} (cartoon)`,
					`${cleanName} (anime)`,
					cleanName
				];

				for (const title of possibleTitles) {
					const directUrl = `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(title)}&prop=pageimages&format=json&pithumbsize=600&redirects=1&origin=*`;
					const directRes = await fetch(directUrl);
					const directData = await directRes.json();

					if (directData.query && directData.query.pages) {
						const pages = directData.query.pages;
						const pageId = Object.keys(pages)[0];
						const page: any = pages[pageId];
						if (pageId !== '-1' && page.thumbnail) {
							return page.thumbnail.source;
						}
					}
				}

				// 3. Last Resort: Generator Search
				const queries = [
					`${cleanName} animated character wiki`,
					`${cleanName} (character)`,
					`${cleanName} cartoon`
				];

				for (const query of queries) {
					const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(query)}&gsrlimit=5&prop=pageimages&format=json&pithumbsize=600&origin=*`;
					const searchRes = await fetch(searchUrl);
					const searchData = await searchRes.json();

					if (searchData.query && searchData.query.pages) {
						const results = Object.values(searchData.query.pages) as any[];
						const target = cleanName.toLowerCase();
						const firstWord = target.split(' ')[0];

						for (const page of results) {
							const title = page.title.toLowerCase();
							if (title.includes(firstWord) || title.includes(target)) {
								if (page.thumbnail) return page.thumbnail.source;
							}
						}
					}
				}
			}
			return null;
		} catch (err) {
			console.error('Image fetch error:', err);
			return null;
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
				const detectedAge = topFace.age;

				const actorPromises = topFace.actor_matches.map(async (m: any) => ({
					name: m.name,
					confidence: m.confidence,
					image: await fetchCelebImage(m.name, detectedAge, 'actor')
				}));

				const cartoonPromises = topFace.cartoon_matches.map(async (m: any) => ({
					name: m.name,
					confidence: m.confidence,
					image: await fetchCelebImage(m.name, detectedAge, 'cartoon')
				}));

				actors = await Promise.all(actorPromises);
				cartoons = await Promise.all(cartoonPromises);
				selectedMatch = actors[0] || cartoons[0] || null;
				manualSelectedImage = null; // Clear manual image on new search
				resultsFound = true;
			}
		} catch (err) {
			console.error('Backend Error:', err);
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
		manualSelectedImage = null;
		projectedMatch = null;
		projectedManualImage = null;
		showOnTV = false;
		projectionStep = 0;
		// Also clear search state
		searchQuery = '';
		searchResults = [];
		searchMode = false;
	}

	// ---- SEARCH FEATURE ----
	// Searches Wikipedia for top 10 celebrities/cartoons matching the query,
	// fetches their images, and loads them into the result grid.
	async function handleSearch() {
		const query = searchQuery.trim();
		if (!query) return;

		isSearching = true;
		searchMode = true;
		searchResults = [];
		selectedMatch = null;
		manualSelectedImage = null;

		try {
			// Step 1: Use Wikipedia opensearch to get candidate titles
			const opensearchUrl = `https://en.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=20&format=json&origin=*`;
			const openRes = await fetch(opensearchUrl);
			const openData = await openRes.json();

			// openData is [query, [titles], [descriptions], [urls]]
			const candidateTitles: string[] = (openData[1] as string[]) || [];

			// Step 2: Also run a generator search to get more candidates
			const genUrl = `https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch=${encodeURIComponent(query)}&gsrlimit=20&prop=pageimages|extracts&exintro=1&exsentences=1&explaintext=1&format=json&pithumbsize=600&origin=*`;
			const genRes = await fetch(genUrl);
			const genData = await genRes.json();

			// Collect titles from generator search (sorted by relevance index)
			let genPages: any[] = [];
			if (genData.query && genData.query.pages) {
				genPages = Object.values(genData.query.pages) as any[];
				genPages.sort((a: any, b: any) => a.index - b.index);
			}

			// Merge: opensearch titles first (most relevant), then generator pages not already included
			const seenTitles = new Set<string>();
			const mergedTitles: string[] = [];

			for (const t of candidateTitles) {
				if (!seenTitles.has(t.toLowerCase())) {
					seenTitles.add(t.toLowerCase());
					mergedTitles.push(t);
				}
			}
			for (const p of genPages) {
				if (!seenTitles.has(p.title.toLowerCase())) {
					seenTitles.add(p.title.toLowerCase());
					mergedTitles.push(p.title);
				}
			}

			// Step 3: For top candidates, fetch images in parallel
			// We'll attempt up to 20 to guarantee we find 10 with images
			const topCandidates = mergedTitles.slice(0, 20);

			const imagePromises = topCandidates.map(async (title) => {
				try {
					const imgUrl = `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(title)}&prop=pageimages|extracts&exintro=1&exsentences=1&explaintext=1&format=json&pithumbsize=600&redirects=1&origin=*`;
					const imgRes = await fetch(imgUrl);
					const imgData = await imgRes.json();

					if (imgData.query && imgData.query.pages) {
						const pages = imgData.query.pages;
						const pageId = Object.keys(pages)[0];
						const page: any = pages[pageId];
						if (pageId !== '-1') {
							return {
								name: page.title,
								confidence: 1.0,
								image: page.thumbnail?.source || null,
								extract: page.extract || ''
							};
						}
					}
				} catch (e) {
					// silently skip failed fetches
				}
				return null;
			});

			const allResults = await Promise.all(imagePromises);

			// Filter nulls, keep up to 10
			searchResults = allResults
				.filter((r): r is NonNullable<typeof r> => r !== null)
				.slice(0, 10);

			// Auto-select the first result
			if (searchResults.length > 0) {
				selectedMatch = searchResults[0];
			}
		} catch (err) {
			console.error('Search error:', err);
		} finally {
			isSearching = false;
		}
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') handleSearch();
	}

	function clearSearch() {
		searchQuery = '';
		searchResults = [];
		searchMode = false;
		selectedMatch = actors[0] || cartoons[0] || null;
	}

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (file) processManualImage(file);
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		const file = event.dataTransfer?.files[0];
		if (file && selectedMatch) processManualImage(file);
	}

	function processManualImage(file: File) {
		const reader = new FileReader();
		reader.onload = (e) => {
			manualSelectedImage = e.target?.result as string;
		};
		reader.readAsDataURL(file);
	}

	function startProjection() {
		if (!selectedMatch) return;

		// Freeze the current selection for the TV screen
		projectedMatch = { ...selectedMatch };
		projectedManualImage = manualSelectedImage;

		showOnTV = true;
		projectionStep = 1;
		setTimeout(() => {
			if (showOnTV) projectionStep = 2;
		}, 2500);
	}

	function selectMatch(item: any) {
		selectedMatch = item;
		manualSelectedImage = null; // Reset manual image for the preview when a new item is selected
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
				{#if showOnTV && projectedMatch}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="tv-projection-container step-{projectionStep}"
						ondragover={(e) => e.preventDefault()}
						ondrop={handleDrop}
					>
						<div class="projection-part live-side">
							<div class="avatar-medium">
								<!-- svelte-ignore a11y_media_has_caption -->
								<video bind:this={tvVideoElement} autoplay playsinline class="webcam-video"></video>
							</div>
						</div>
						<div class="projection-part arrow-side"><div class="big-arrow">&gt;</div></div>
						<div class="projection-part match-side">
							<div class={projectionStep === 1 ? 'avatar-large' : 'avatar-medium'}>
								{#if projectedManualImage || projectedMatch.image}
									<img
										src={projectedManualImage || projectedMatch.image}
										alt={projectedMatch.name}
										class="avatar-img"
									/>
								{/if}
							</div>
						</div>
					</div>
				{:else}
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="idle-message" ondragover={(e) => e.preventDefault()} ondrop={handleDrop}>
						<p style="font-size: 0.6rem; letter-spacing: 3px; opacity: 0.2">
							{resultsFound ? 'SELECT A MATCH' : 'WAITING FOR INPUT'}
						</p>
					</div>
				{/if}
			</VideoPanel>
		</div>

		<div class="right-column">
			<!-- Search Bar Row -->
			<div class="search-row">
				<div class="search-input-wrap">
					<svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="11" cy="11" r="8"/>
						<line x1="21" y1="21" x2="16.65" y2="16.65"/>
					</svg>
					<input
						id="celeb-search-input"
						type="text"
						class="search-input"
						placeholder="Search any celebrity or cartoon…"
						bind:value={searchQuery}
						onkeydown={handleSearchKeydown}
						disabled={isSearching}
					/>
					{#if searchMode}
						<button class="clear-btn" onclick={clearSearch} title="Clear search">
							<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="14" height="14">
								<line x1="18" y1="6" x2="6" y2="18"/>
								<line x1="6" y1="6" x2="18" y2="18"/>
							</svg>
						</button>
					{/if}
				</div>
				<AppButton
					variant="primary"
					onclick={handleSearch}
					disabled={isSearching || !searchQuery.trim()}
					style="min-width: 100px;"
				>
					{isSearching ? 'Searching…' : 'Search'}
				</AppButton>
			</div>

			<div class="controls-row">
				{#if capturedImage}<AppButton variant="secondary" onclick={handleReset}>Reset Cam</AppButton
					>{/if}
				<AppButton
					variant="primary"
					onclick={handleFind}
					disabled={isFinding}
					style="min-width: 180px;"
				>
					{isFinding ? 'Analyzing...' : 'Find Matches'}
				</AppButton>
			</div>

			<div class="unified-results-grid">
				<!-- Results Section -->
				{#if isSearching}
					<!-- Searching shimmer -->
					{#each Array(10) as _}<ResultCard type="skeleton" shimmer />{/each}
				{:else if searchMode && searchResults.length > 0}
					<!-- Search results mode -->
					{#each searchResults as result}
						<ResultCard
							item={result}
							type="actor"
							selected={selectedMatch === result}
							onclick={() => selectMatch(result)}
						/>
					{/each}
					<!-- Fill remaining slots with skeletons if fewer than 10 results -->
					{#each Array(Math.max(0, 10 - searchResults.length)) as _}<ResultCard type="skeleton" />{/each}
				{:else if searchMode && searchResults.length === 0 && !isSearching}
					<!-- No results found -->
					{#each Array(10) as _}<ResultCard type="skeleton" />{/each}
				{:else if !resultsFound && !isFinding}
					<!-- Default idle state -->
					{#each Array(10) as _}<ResultCard type="skeleton" />{/each}
				{:else if isFinding}
					<!-- AI analyzing -->
					{#each Array(10) as _}<ResultCard type="skeleton" shimmer />{/each}
				{:else}
					<!-- AI results mode -->
					{#each actors as actor}
						<ResultCard
							item={actor}
							type="actor"
							selected={selectedMatch === actor}
							onclick={() => selectMatch(actor)}
						/>
					{/each}
					{#each cartoons as cartoon}
						<ResultCard
							item={cartoon}
							type="cartoon"
							selected={selectedMatch === cartoon}
							onclick={() => selectMatch(cartoon)}
						/>
					{/each}
				{/if}

				<!-- Selection Preview Dashboard (Integrated into Grid) -->
				<div class="settings-card integrated">
					<div class="card-header">SELECTION PREVIEW</div>
					<div class="card-body-horizontal">
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div class="preview-area" ondragover={(e) => e.preventDefault()} ondrop={handleDrop}>
							{#if selectedMatch}
								<div class="preview-img-box">
									{#if manualSelectedImage || selectedMatch.image}
										<img
											src={manualSelectedImage || selectedMatch.image}
											alt={selectedMatch.name}
											class="avatar-img"
										/>
									{:else}
										<div class="avatar-placeholder"></div>
									{/if}
								</div>
								<div class="preview-info">
									{#if !manualSelectedImage}
										<span class="preview-name">{selectedMatch.name}</span>
										<span class="preview-conf"
											>{Math.round(selectedMatch.confidence * 100)}% Match</span
										>
									{:else}
										<span class="preview-name" style="opacity: 0.3">Custom Selection</span>
									{/if}
								</div>
							{:else}
								<div class="empty-preview"><p>No person selected</p></div>
							{/if}
						</div>

						<div class="preview-actions">
							<AppButton
								variant="secondary"
								onclick={() => document.getElementById('celeb-upload')?.click()}
								disabled={!selectedMatch}
								style="flex: 1;"
							>
								CHANGE IMAGE
							</AppButton>
							<input
								type="file"
								id="celeb-upload"
								style="display: none;"
								accept="image/*"
								onchange={handleFileSelect}
							/>

							<AppButton
								variant="primary"
								onclick={startProjection}
								disabled={!selectedMatch}
								style="flex: 2; background: var(--accent-color); color: #000;"
							>
								SHOW LIVE
							</AppButton>
						</div>
					</div>
				</div>
			</div>
		</div>
	</main>
</div>

<style>
	/* ---- Search Bar Styles ---- */
	.search-row {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 10px;
	}

	.search-input-wrap {
		flex: 1;
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		width: 15px;
		height: 15px;
		color: rgba(255, 255, 255, 0.35);
		pointer-events: none;
		flex-shrink: 0;
	}

	.search-input {
		width: 100%;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		color: #fff;
		font-size: 0.8rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		padding: 10px 36px 10px 36px;
		outline: none;
		transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
		font-family: inherit;
	}

	.search-input::placeholder {
		color: rgba(255, 255, 255, 0.25);
	}

	.search-input:focus {
		border-color: rgba(0, 255, 136, 0.5);
		background: rgba(255, 255, 255, 0.07);
		box-shadow: 0 0 0 3px rgba(0, 255, 136, 0.08);
	}

	.search-input:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.clear-btn {
		position: absolute;
		right: 10px;
		background: none;
		border: none;
		cursor: pointer;
		color: rgba(255, 255, 255, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3px;
		border-radius: 4px;
		transition: color 0.15s;
	}

	.clear-btn:hover {
		color: rgba(255, 255, 255, 0.9);
	}

	/* ---- Controls Row ---- */
	.controls-row {
		display: flex;
		justify-content: flex-end;
		gap: 12px;
		align-items: center;
	}
	.unified-results-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 12px;
		margin-top: 15px;
	}

	.settings-card.integrated {
		grid-column: span 5;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid var(--border-color);
		border-radius: 12px;
		padding: 15px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		margin-top: 10px;
	}

	.card-body-horizontal {
		display: flex;
		align-items: center;
		gap: 20px;
	}

	.preview-area {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 15px;
		background: rgba(0, 0, 0, 0.2);
		padding: 10px 15px;
		border-radius: 8px;
		border: 1px solid rgba(255, 255, 255, 0.05);
	}

	.preview-actions {
		flex: 1;
		display: flex;
		gap: 10px;
	}
	.preview-img-box {
		width: 60px;
		height: 60px;
		border-radius: 6px;
		overflow: hidden;
		border: 1px solid rgba(255, 255, 255, 0.1);
		background: #111;
	}
	.preview-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.preview-name {
		font-size: 0.9rem;
		font-weight: 800;
		color: #fff;
	}
	.preview-conf {
		font-size: 0.7rem;
		color: var(--accent-color);
		font-weight: 600;
	}
	.empty-preview {
		height: 60px;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 100%;
		font-size: 0.7rem;
		opacity: 0.4;
	}
	.card-header {
		font-size: 0.75rem;
		font-weight: 900;
		letter-spacing: 2px;
		opacity: 0.5;
		margin-bottom: 5px;
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
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(100%);
		}
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
	.avatar-img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.idle-message {
		text-align: center;
	}
</style>
