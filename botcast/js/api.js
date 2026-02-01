// ==========================================
// BotCast - API Integration & Audio Control
// ==========================================

const API_BASE = 'http://localhost:5000/api';

// Audio context
let audioContext = null;
let audioElement = null;
let generatedEpisodes = {};

// Initialize audio context
function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

// ==================== API Calls ====================

/**
 * Fetch hosts from backend
 */
async function fetchHosts() {
    try {
        const response = await fetch(`${API_BASE}/hosts`);
        const data = await response.json();
        return data.hosts || [];
    } catch (error) {
        console.error('Error fetching hosts:', error);
        return botHosts; // Fallback to local data
    }
}

/**
 * Fetch podcasts from backend
 */
async function fetchPodcasts() {
    try {
        const response = await fetch(`${API_BASE}/podcasts`);
        const data = await response.json();
        return data.podcasts || [];
    } catch (error) {
        console.error('Error fetching podcasts:', error);
        return podcasts; // Fallback to local data
    }
}

/**
 * Fetch episodes for specific podcast
 */
async function fetchEpisodes(podcastId) {
    try {
        const response = await fetch(`${API_BASE}/episodes/${podcastId}`);
        const data = await response.json();
        return data.episodes || [];
    } catch (error) {
        console.error('Error fetching episodes:', error);
        return [];
    }
}

/**
 * Generate speech from text
 */
async function generateSpeech(text, hostId = 'nova') {
    try {
        const response = await fetch(`${API_BASE}/generate-speech`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                host_id: hostId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.status === 'success') {
            return data.audio_file;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error generating speech:', error);
        return null;
    }
}

/**
 * Generate episode audio
 */
async function generateEpisodeAudio(episodeId) {
    try {
        // Show loading indicator
        showLoadingIndicator(`Generating audio for episode...`);
        
        const response = await fetch(`${API_BASE}/generate-episode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                episode_id: episodeId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }
        
        const data = await response.json();
        hideLoadingIndicator();
        
        if (data.status === 'success') {
            generatedEpisodes[episodeId] = data.episode;
            return data.episode;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error generating episode:', error);
        hideLoadingIndicator();
        showError(`Failed to generate episode: ${error.message}`);
        return null;
    }
}

/**
 * Get episode audio URL
 */
function getEpisodeAudioUrl(audioFile) {
    const filename = audioFile.split('/').pop();
    return `${API_BASE}/audio/${filename}`;
}

/**
 * Search podcasts and hosts
 */
async function searchContent(query) {
    try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.results || { podcasts: [], hosts: [] };
    } catch (error) {
        console.error('Error searching:', error);
        return { podcasts: [], hosts: [] };
    }
}

// ==================== Audio Playback ====================

/**
 * Play episode with generated audio
 */
async function playEpisodeWithAudio(episodeId) {
    try {
        // Get or generate episode audio
        let episode = generatedEpisodes[episodeId];
        
        if (!episode) {
            episode = await generateEpisodeAudio(episodeId);
            if (!episode) return;
        }
        
        // Create or get audio element
        if (!audioElement) {
            audioElement = new Audio();
            audioElement.addEventListener('ended', onAudioEnded);
            audioElement.addEventListener('timeupdate', onAudioTimeUpdate);
        }
        
        // Play first audio file
        if (episode.audio_files && episode.audio_files.length > 0) {
            const audioUrl = getEpisodeAudioUrl(episode.audio_files[0]);
            audioElement.src = audioUrl;
            audioElement.play();
            
            // Update UI
            updatePlayerUI(episode);
            showPlaybackControls();
        }
    } catch (error) {
        console.error('Error playing episode:', error);
        showError('Failed to play episode');
    }
}

/**
 * Play generated speech directly
 */
async function playSpeech(text, hostId = 'nova') {
    try {
        showLoadingIndicator('Generating speech...');
        
        const audioFile = await generateSpeech(text, hostId);
        hideLoadingIndicator();
        
        if (!audioFile) return;
        
        // Create or get audio element
        if (!audioElement) {
            audioElement = new Audio();
            audioElement.addEventListener('ended', onAudioEnded);
        }
        
        const audioUrl = getEpisodeAudioUrl(audioFile);
        audioElement.src = audioUrl;
        audioElement.play();
        
        showPlaybackControls();
    } catch (error) {
        console.error('Error playing speech:', error);
        hideLoadingIndicator();
        showError('Failed to play speech');
    }
}

/**
 * Stop audio playback
 */
function stopAudio() {
    if (audioElement) {
        audioElement.pause();
        audioElement.currentTime = 0;
    }
}

/**
 * Toggle audio playback
 */
function toggleAudioPlayback() {
    if (!audioElement) return;
    
    if (audioElement.paused) {
        audioElement.play();
        updatePlayButton('pause');
    } else {
        audioElement.pause();
        updatePlayButton('play');
    }
}

/**
 * Set playback speed
 */
function setPlaybackSpeed(speed) {
    if (audioElement) {
        audioElement.playbackRate = speed;
    }
}

/**
 * Seek to specific time
 */
function seekAudio(time) {
    if (audioElement) {
        audioElement.currentTime = time;
    }
}

// ==================== Event Handlers ====================

function onAudioEnded() {
    updatePlayButton('play');
    showNotification('Episode ended');
}

function onAudioTimeUpdate() {
    if (audioElement) {
        updateProgressBar(audioElement.currentTime, audioElement.duration);
    }
}

// ==================== UI Helpers ====================

function showLoadingIndicator(message = 'Loading...') {
    let indicator = document.getElementById('loading-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'loading-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 30px 50px;
            border-radius: 10px;
            z-index: 9999;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 15px;
        `;
        document.body.appendChild(indicator);
    }
    
    indicator.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        <span>${message}</span>
    `;
    indicator.style.display = 'flex';
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #ef4444;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

function showPlaybackControls() {
    const controls = document.getElementById('playback-controls');
    if (controls) {
        controls.style.display = 'flex';
    }
}

function updatePlayButton(state) {
    const playBtn = document.getElementById('play-btn');
    if (playBtn) {
        if (state === 'play') {
            playBtn.innerHTML = '<i class="fas fa-play"></i>';
        } else {
            playBtn.innerHTML = '<i class="fas fa-pause"></i>';
        }
    }
}

function updateProgressBar(current, duration) {
    const progressBar = document.getElementById('progress-bar');
    if (progressBar && duration) {
        const percent = (current / duration) * 100;
        progressBar.style.width = percent + '%';
    }
    
    const timeDisplay = document.getElementById('current-time');
    if (timeDisplay) {
        timeDisplay.textContent = formatTime(current);
    }
}

function updatePlayerUI(episode) {
    const title = document.getElementById('player-title');
    if (title) {
        title.textContent = episode.title;
    }
    
    const description = document.getElementById('player-description');
    if (description) {
        description.textContent = episode.description || '';
    }
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 20px;
        background: #10b981;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 9999;
        animation: slideUp 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function formatTime(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ==================== Health Check ====================

/**
 * Check if backend is available
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('✅ Backend health:', data);
        return true;
    } catch (error) {
        console.warn('⚠️ Backend not available:', error);
        return false;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🤖 BotCast API Module Loaded');
    checkBackendHealth();
});
