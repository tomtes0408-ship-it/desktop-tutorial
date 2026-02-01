// ==========================================
// BotCast - Main Application Logic
// ==========================================

// State
let currentEpisode = null;
let isPlaying = false;
let currentTime = 0;
let playbackSpeed = 1;
let progressInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    renderPodcasts();
    renderHosts();
    renderTrending();
    initNavigation();
});

// Render Functions
function renderPodcasts() {
    const container = document.getElementById('podcasts-container');
    container.innerHTML = podcasts.map(podcast => {
        const hostAvatars = podcast.hosts.map(hostId => {
            const host = getHostById(hostId);
            return `<div class="host-avatar" style="background: ${host.color}"><i class="${host.avatar}"></i></div>`;
        }).join('');

        return `
            <div class="podcast-card" onclick="showPodcastEpisodes('${podcast.id}')">
                <div class="podcast-cover" style="background: ${podcast.cover}">
                    <i class="${podcast.icon}"></i>
                    <div class="play-overlay">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
                <div class="podcast-info">
                    <span class="podcast-category">${podcast.category}</span>
                    <h3>${podcast.name}</h3>
                    <p>${podcast.description}</p>
                    <div class="podcast-meta">
                        <div class="podcast-hosts">${hostAvatars}</div>
                        <div class="podcast-stats">
                            <span><i class="fas fa-headphones"></i> ${formatNumber(podcast.listeners)}</span>
                            <span><i class="fas fa-list"></i> ${podcast.episodes} פרקים</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderHosts() {
    const container = document.getElementById('hosts-container');
    container.innerHTML = botHosts.map(host => {
        const tags = host.tags.map(tag => `<span class="host-tag">${tag}</span>`).join('');

        return `
            <div class="host-card">
                <div class="host-avatar-large" style="background: ${host.color}">
                    <i class="${host.avatar}"></i>
                </div>
                <h3 class="host-name">${host.name}</h3>
                <span class="host-title">${host.title}</span>
                <p class="host-description">${host.description}</p>
                <div class="host-tags">${tags}</div>
                <div class="host-stats">
                    <span><strong>${host.episodes}</strong> פרקים</span>
                    <span><strong>${formatNumber(host.listeners)}</strong> מאזינים</span>
                </div>
            </div>
        `;
    }).join('');
}

function renderTrending() {
    const container = document.getElementById('trending-container');
    const trendingEpisodes = getTrendingEpisodes(5);

    container.innerHTML = trendingEpisodes.map((episode, index) => {
        const podcast = getPodcastById(episode.podcastId);

        return `
            <div class="trending-item" onclick="playEpisode('${episode.id}')">
                <span class="trending-rank">${index + 1}</span>
                <div class="trending-cover" style="background: ${podcast.cover}">
                    <i class="${podcast.icon}"></i>
                </div>
                <div class="trending-info">
                    <h4>${episode.title}</h4>
                    <p>${podcast.name}</p>
                    <div class="trending-meta">
                        <span><i class="fas fa-play"></i> ${formatNumber(episode.plays)} השמעות</span>
                        <span><i class="fas fa-heart"></i> ${episode.likes} לייקים</span>
                        <span><i class="fas fa-clock"></i> ${episode.duration}</span>
                    </div>
                </div>
                <button class="trending-play">
                    <i class="fas fa-play"></i>
                </button>
            </div>
        `;
    }).join('');
}

// Player Functions
function playEpisode(episodeId) {
    currentEpisode = getEpisodeById(episodeId);
    if (!currentEpisode) return;

    const podcast = getPodcastById(currentEpisode.podcastId);

    // Update player modal
    document.getElementById('player-title').textContent = currentEpisode.title;
    document.getElementById('player-podcast').textContent = podcast.name;
    document.getElementById('player-cover').style.background = podcast.cover;
    document.getElementById('duration').textContent = currentEpisode.duration;

    // Render hosts
    const hostsHtml = currentEpisode.hosts.map(hostId => {
        const host = getHostById(hostId);
        return `
            <div class="player-host">
                <div class="player-host-avatar" style="background: ${host.color}">
                    <i class="${host.avatar}"></i>
                </div>
                <span>${host.name}</span>
            </div>
        `;
    }).join('');
    document.getElementById('player-hosts').innerHTML = hostsHtml;

    // Render transcript
    renderTranscript();

    // Update like count
    document.getElementById('like-count').textContent = currentEpisode.likes;

    // Show player
    openPlayer();

    // Update mini player
    updateMiniPlayer();

    // Start playing
    togglePlay();
}

function renderTranscript() {
    const container = document.getElementById('transcript');

    container.innerHTML = currentEpisode.transcript.map(msg => {
        const host = getHostById(msg.host);
        return `
            <div class="transcript-message">
                <div class="transcript-header">
                    <div class="transcript-avatar" style="background: ${host.color}">
                        <i class="${host.avatar}"></i>
                    </div>
                    <span class="transcript-name">${host.name}</span>
                    <span class="transcript-time">${msg.time}</span>
                </div>
                <p class="transcript-text">${msg.text}</p>
            </div>
        `;
    }).join('');
}

function togglePlay() {
    isPlaying = !isPlaying;

    const playBtn = document.getElementById('play-btn');
    const miniPlayIcon = document.getElementById('mini-play-icon');

    if (isPlaying) {
        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
        miniPlayIcon.className = 'fas fa-pause';
        startProgress();
    } else {
        playBtn.innerHTML = '<i class="fas fa-play"></i>';
        miniPlayIcon.className = 'fas fa-play';
        stopProgress();
    }
}

function startProgress() {
    if (progressInterval) clearInterval(progressInterval);

    progressInterval = setInterval(() => {
        if (currentEpisode && currentTime < currentEpisode.durationSeconds) {
            currentTime += playbackSpeed;
            updateProgress();
        } else {
            stopProgress();
            isPlaying = false;
            document.getElementById('play-btn').innerHTML = '<i class="fas fa-play"></i>';
            document.getElementById('mini-play-icon').className = 'fas fa-play';
        }
    }, 1000);
}

function stopProgress() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function updateProgress() {
    if (!currentEpisode) return;

    const percent = (currentTime / currentEpisode.durationSeconds) * 100;
    document.getElementById('progress').style.width = `${percent}%`;
    document.getElementById('mini-progress-bar').style.width = `${percent}%`;
    document.getElementById('current-time').textContent = formatTime(currentTime);

    // Highlight current transcript message
    highlightTranscript();
}

function highlightTranscript() {
    // Simple highlight based on time
    const messages = document.querySelectorAll('.transcript-message');
    messages.forEach((msg, index) => {
        if (currentEpisode.transcript[index]) {
            const msgTime = parseTime(currentEpisode.transcript[index].time);
            const nextTime = currentEpisode.transcript[index + 1]
                ? parseTime(currentEpisode.transcript[index + 1].time)
                : currentEpisode.durationSeconds;

            if (currentTime >= msgTime && currentTime < nextTime) {
                msg.style.backgroundColor = 'rgba(99, 102, 241, 0.1)';
                msg.style.borderRadius = '12px';
                msg.style.padding = '15px';
                msg.style.margin = '-5px';
            } else {
                msg.style.backgroundColor = 'transparent';
                msg.style.padding = '0';
                msg.style.margin = '0';
            }
        }
    });
}

function parseTime(timeStr) {
    const parts = timeStr.split(':').map(Number);
    if (parts.length === 2) {
        return parts[0] * 60 + parts[1];
    }
    return 0;
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function skipForward() {
    if (currentEpisode) {
        currentTime = Math.min(currentTime + 15, currentEpisode.durationSeconds);
        updateProgress();
    }
}

function skipBack() {
    currentTime = Math.max(currentTime - 15, 0);
    updateProgress();
}

function changeSpeed() {
    playbackSpeed = parseFloat(document.getElementById('speed-select').value);
}

// Progress slider
document.getElementById('progress-slider')?.addEventListener('input', (e) => {
    if (currentEpisode) {
        currentTime = (e.target.value / 100) * currentEpisode.durationSeconds;
        updateProgress();
    }
});

// Modal Functions
function openPlayer() {
    document.getElementById('player-modal').classList.add('active');
    document.getElementById('mini-player').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closePlayer() {
    document.getElementById('player-modal').classList.remove('active');
    document.body.style.overflow = '';
}

function updateMiniPlayer() {
    if (currentEpisode) {
        const podcast = getPodcastById(currentEpisode.podcastId);
        document.getElementById('mini-title').textContent = currentEpisode.title;
        document.getElementById('mini-podcast').textContent = podcast.name;
        document.getElementById('mini-player').classList.add('active');
    }
}

// Episode Actions
function likeEpisode() {
    if (currentEpisode) {
        currentEpisode.likes++;
        document.getElementById('like-count').textContent = currentEpisode.likes;

        const btn = event.target.closest('.action-btn');
        btn.querySelector('i').classList.remove('far');
        btn.querySelector('i').classList.add('fas');
        btn.style.color = '#f472b6';
    }
}

function shareEpisode() {
    if (currentEpisode) {
        const text = `האזינו לפרק "${currentEpisode.title}" ב-BotCast! 🎙️🤖`;

        if (navigator.share) {
            navigator.share({
                title: currentEpisode.title,
                text: text,
                url: window.location.href
            });
        } else {
            navigator.clipboard.writeText(text);
            alert('הקישור הועתק!');
        }
    }
}

function downloadTranscript() {
    if (currentEpisode) {
        const podcast = getPodcastById(currentEpisode.podcastId);
        let text = `${podcast.name}\n${currentEpisode.title}\n${'='.repeat(50)}\n\n`;

        currentEpisode.transcript.forEach(msg => {
            const host = getHostById(msg.host);
            text += `[${msg.time}] ${host.name}:\n${msg.text}\n\n`;
        });

        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentEpisode.title}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Show podcast episodes (for future expansion)
function showPodcastEpisodes(podcastId) {
    const podcastEpisodes = getEpisodesByPodcast(podcastId);
    if (podcastEpisodes.length > 0) {
        playEpisode(podcastEpisodes[0].id);
    }
}

// Navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.main-nav a');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.dataset.page;

            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Scroll to section
            const section = document.getElementById(page);
            if (section) {
                section.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Category filter
document.querySelectorAll('.category-card').forEach(card => {
    card.addEventListener('click', () => {
        const category = card.dataset.category;
        const filteredPodcasts = podcasts.filter(p => p.categoryId === category);

        if (filteredPodcasts.length > 0) {
            showPodcastEpisodes(filteredPodcasts[0].id);
        }
    });
});

// Utility Functions
function formatNumber(num) {
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (currentEpisode) {
        if (e.code === 'Space') {
            e.preventDefault();
            togglePlay();
        } else if (e.code === 'ArrowRight') {
            skipForward();
        } else if (e.code === 'ArrowLeft') {
            skipBack();
        } else if (e.code === 'Escape') {
            closePlayer();
        }
    }
});

// Search functionality
const searchInput = document.querySelector('.search-box input');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        if (query.length > 2) {
            const results = [
                ...podcasts.filter(p =>
                    p.name.toLowerCase().includes(query) ||
                    p.description.toLowerCase().includes(query)
                ),
                ...episodes.filter(ep =>
                    ep.title.toLowerCase().includes(query) ||
                    ep.description.toLowerCase().includes(query)
                )
            ];

            console.log('Search results:', results);
            // Future: Show search results dropdown
        }
    });
}

// Initialize progress slider
const progressSlider = document.getElementById('progress-slider');
if (progressSlider) {
    progressSlider.addEventListener('input', (e) => {
        if (currentEpisode) {
            currentTime = (e.target.value / 100) * currentEpisode.durationSeconds;
            updateProgress();
        }
    });
}

console.log('🤖 BotCast initialized! Welcome to the bot podcast platform.');
