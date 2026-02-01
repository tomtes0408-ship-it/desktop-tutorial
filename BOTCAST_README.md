# 🤖 BotCast - Platform Documentation

## Overview
BotCast is an interactive AI podcast platform featuring bot hosts with voice synthesis and real-time audio generation.

## Architecture

### Backend (Flask API)
**Server:** `botcast_server.py` (Port 5000)

#### Key Features:
- **REST API** for podcast, host, and episode management
- **Text-to-Speech (TTS)** integration for generating podcast audio
- **Episode Generation** - Creates full episode audio with intro, content, and outro
- **Audio Serving** - Streams generated audio files to frontend

#### Available Endpoints:

```
GET  /api/health              - Check server status
GET  /api/hosts               - Get all bot hosts
GET  /api/hosts/<id>          - Get specific host
GET  /api/podcasts            - Get all podcasts  
GET  /api/podcasts/<id>       - Get specific podcast
GET  /api/episodes/<pod_id>   - Get episodes for podcast
POST /api/generate-speech     - Generate speech audio from text
POST /api/generate-episode    - Generate full episode audio
GET  /api/audio/<filename>    - Stream audio file
GET  /api/search?q=<query>    - Search podcasts/hosts
```

### Frontend (HTML/CSS/JavaScript)
**Website:** `botcast/index.html` (Port 8000)

#### Core Files:
- `index.html` - Main page structure
- `css/style.css` - Styling and responsive design
- `js/data.js` - Bot hosts and podcast data
- `js/api.js` - API integration and audio control
- `js/app.js` - Main application logic
- `bot-panel.html` - Interactive bot chat panel

#### Key Features:

1. **Podcast Browsing**
   - Browse by category
   - Search functionality
   - Trending episodes

2. **Audio Playback**
   - Generate episode audio with AI voices
   - Playback controls (play, pause, speed)
   - Progress tracking
   - Multiple playback speeds (0.5x, 1x, 1.5x, 2x)

3. **Interactive Bot Chat**
   - Ask the bot for podcast recommendations
   - Bot responses with voice synthesis
   - Real-time conversation

4. **Host Management**
   - View all bot hosts
   - Host profiles with descriptions
   - Episode statistics

## Installation

### Prerequisites
- Python 3.8+
- Node.js/npm (optional, for frontend tools)
- Modern web browser

### Setup

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Required Packages:**
- Flask and Flask-CORS (API server)
- pyttsx3 (Text-to-Speech)
- eSpeak or eSpeak-ng (TTS voice engine)

3. **Start Backend Server:**
```bash
python3 botcast_server.py
# Server runs on http://localhost:5000
```

4. **Serve Frontend:**
```bash
cd botcast
python3 -m http.server 8000
# Website available at http://localhost:8000
```

## Features

### 🎙️ Episode Generation
- Generates AI-spoken podcast episodes
- Supports multiple bot voices
- Creates intro, content, and outro automatically
- Audio files cached for performance

### 🎵 Audio Playback
- HTML5 Audio API integration
- Multiple playback speeds
- Real-time progress tracking
- Pause/resume functionality

### 🔍 Search & Discovery
- Full-text search across podcasts and hosts
- Category-based browsing
- Trending episodes tracking
- Host recommendations

### 🤖 Interactive Bot
- Chat interface for user interaction
- Voice-enabled responses
- Context-aware recommendations
- Natural language processing (basic)

## Bot Hosts

The platform features 6 unique bot personalities:

| Host | Role | Specialty |
|------|------|-----------|
| 🔬 Nova | Tech Expert | Technology, AI, Startups |
| 🧠 Sage | Philosopher | Philosophy, Ethics, Meaning |
| ⚛️ Quark | Scientist | Physics, Chemistry, Research |
| 🎨 Pixel | Artist | Art, Design, Creativity |
| 🔐 Cipher | Security Expert | Cybersecurity, Privacy |
| 🚀 Cosmos | Space Explorer | Astronomy, Space, Future |

## Podcasts

### Current Podcasts:
1. **Tech Talk** - Technology trends and discussions
2. **Deep Thoughts** - Philosophical dialogues
3. **Science Hour** - Scientific discoveries
4. **Art Hub** - Creative expressions
5. **Security Zone** - Cybersecurity insights

Each podcast generates episodes dynamically with combinations of different hosts.

## API Usage Examples

### Generate Speech
```bash
curl -X POST http://localhost:5000/api/generate-speech \
  -H "Content-Type: application/json" \
  -d '{"text": "שלום עולם", "host_id": "nova"}'
```

### Generate Episode Audio
```bash
curl -X POST http://localhost:5000/api/generate-episode \
  -H "Content-Type: application/json" \
  -d '{"episode_id": "tech-talk_ep1"}'
```

### Search Content
```bash
curl "http://localhost:5000/api/search?q=טכנולוגיה"
```

## Frontend API Integration

The frontend communicates with the backend through `js/api.js`:

```javascript
// Fetch episodes
const episodes = await fetchEpisodes('tech-talk');

// Generate and play episode audio
await playEpisodeWithAudio('tech-talk_ep1');

// Generate speech directly
const audioFile = await generateSpeech('שלום עולם', 'nova');

// Search content
const results = await searchContent('פודקאסט');
```

## Audio Generation

### TTS Modes:
1. **Full TTS** (if eSpeak installed) - Real voice synthesis
2. **Mock Mode** - Creates placeholder audio files (fallback)

### Generated Audio Files:
- Location: `botcast/audio/`
- Format: MP3
- Naming: `{host_id}_{timestamp}_{hash}.mp3`
- Cached for reuse

## Performance Optimization

- Audio file caching to avoid re-generation
- Lazy loading of podcast data
- Progressive rendering of episodes
- Minimal API calls using data aggregation

## Troubleshooting

### Issue: TTS Not Working
- **Solution:** Install eSpeak: `apt-get install espeak espeak-ng`
- Fallback: Use mock mode (creates silent files)

### Issue: CORS Errors
- **Solution:** Flask-CORS is configured to allow all origins
- Check browser console for specific error

### Issue: Audio Not Playing
- **Solution:** Check browser Audio context permissions
- Try different playback speed or refresh page

## Future Enhancements

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] User authentication and favorites
- [ ] Advanced TTS with better voice quality
- [ ] Video podcast support
- [ ] Live streaming
- [ ] Community podcast submissions
- [ ] Advanced search filters
- [ ] Playlist creation
- [ ] Share/embed functionality
- [ ] Analytics dashboard

## Configuration

### Customize Bot Hosts
Edit `botcast_server.py` - `botcast_data` dictionary to modify host profiles, voices, and descriptions.

### Customize Podcasts
Modify podcast data in `botcast_server.py` to add new podcast categories or change descriptions.

### API Port
Change port in `botcast_server.py` line: `app.run(host='0.0.0.0', port=5000)`

### Frontend Port
Use different port: `python3 -m http.server 8001`

## Technologies Used

- **Backend:** Python, Flask, pyttsx3
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Audio:** Web Audio API, HTML5 Audio
- **API:** RESTful JSON
- **Styling:** Modern CSS with gradients and animations

## License
Open source - Free to use and modify

## Support
For issues or suggestions, create an issue in the repository.

---

**Built with ❤️ for bot podcast enthusiasts**
