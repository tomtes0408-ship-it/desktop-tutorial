# 🚀 BotCast Quick Start Guide

## What is BotCast?
BotCast is an AI-powered podcast platform featuring bot hosts with voice synthesis. Listen to podcasts with generated audio, chat with interactive bots, and discover content - all with realistic voice narration!

## ⚡ Quick Start (60 seconds)

### 1️⃣ Start Backend Server (Terminal 1)
```bash
cd /workspaces/desktop-tutorial
python3 botcast_server.py
```
**Expected output:**
```
🤖 BotCast Server is starting...
🚀 Server running at http://localhost:5000
```

### 2️⃣ Start Frontend Server (Terminal 2)
```bash
cd /workspaces/desktop-tutorial/botcast
python3 -m http.server 8000
```
**Expected output:**
```
Serving HTTP on 0.0.0.0 port 8000
```

### 3️⃣ Open Website
Visit: **http://localhost:8000**

---

## 🎯 Features to Try

### 📻 Listen to Podcasts
1. Browse featured podcasts on homepage
2. Click on any podcast card
3. Select an episode
4. Click "Generate Audio" button
5. Listen with playback controls (speed control available!)

### 🤖 Chat with Bot
1. Click the **bot icon** (bottom left)
2. Type your question or request
3. Bot responds with:
   - Podcast recommendations
   - Episode suggestions
   - Helpful information with voice synthesis

### 🔍 Search
1. Use search box at top
2. Search by:
   - Podcast name
   - Host name
   - Category

### 📊 Browse Categories
- Technology 🔬
- Philosophy 🧠  
- Science ⚛️
- Art 🎨
- Security 🔐
- Space 🚀

---

## 🎤 Bot Hosts

Meet the podcast presenters:

| Host | Role | 
|------|------|
| **Nova** 🔬 | Tech expert discussing AI, startups, innovation |
| **Sage** 🧠 | Philosopher exploring ethics and meaning |
| **Quark** ⚛️ | Scientist diving into physics and discovery |
| **Pixel** 🎨 | Artist discussing design and creativity |
| **Cipher** 🔐 | Security expert on cybersecurity |
| **Cosmos** 🚀 | Space explorer discussing astronomy |

---

## 📱 Available Podcasts

1. **Tech Talk** - Technology & Innovation
2. **Deep Thoughts** - Philosophy & Ethics
3. **Science Hour** - Scientific Discovery
4. **Art Hub** - Creative Expression
5. **Security Zone** - Cybersecurity Insights

---

## 🎛️ Playback Controls

### Play/Pause
- Click play button to start episode
- Episode audio is generated automatically
- Click pause to stop

### Speed Control
- Dropdown in playback controls
- Options: 0.5x, 1x, 1.5x, 2x
- Perfect for fast listening!

### Progress Bar
- Shows current playback position
- Click to seek forward/backward
- Time display updates

---

## 🔧 Technical Details

### Backend API (Port 5000)
```
GET  /api/health              → Server status
GET  /api/hosts               → All bot hosts
GET  /api/podcasts            → All podcasts
GET  /api/episodes/<podcast>  → Episodes list
POST /api/generate-speech     → Create audio from text
POST /api/generate-episode    → Create episode audio
GET  /api/search?q=query      → Search content
```

### Frontend (Port 8000)
- Pure HTML5/CSS3/JavaScript
- No build tools required
- Works in any modern browser

### Audio Format
- Generated audio: MP3 format
- Storage: `botcast/audio/` directory
- Playback: HTML5 Audio API

---

## 🎧 Audio Generation

### How It Works:
1. Select episode → Backend generates audio
2. Uses text-to-speech (TTS) engine
3. Audio cached for reuse
4. Streams to browser via API
5. HTML5 Audio element plays it

### Current Mode:
- **Mock TTS** (creates silent files - fallback mode)
- For full voices: Install espeak → Real voice synthesis

### Install Real TTS (Optional):
```bash
# Linux
sudo apt-get install espeak espeak-ng

# macOS  
brew install espeak

# Windows
# Download from: https://espeak.sourceforge.net/
```

---

## 🚀 What's Happening Behind the Scenes?

### Data Flow:
```
Frontend (HTML/JS)
        ↓
  API Requests
        ↓
Flask Backend (Python)
        ↓
TTS Engine (pyttsx3 + espeak)
        ↓
Generate MP3 Audio
        ↓
Save to disk & return URL
        ↓
HTML5 Audio plays it
        ↓
User hears podcast! 🎉
```

---

## 📂 File Structure

```
desktop-tutorial/
├── botcast_server.py              # Flask backend
├── botcast/
│   ├── index.html                 # Main page
│   ├── bot-panel.html             # Bot chat interface
│   ├── css/
│   │   └── style.css              # Styling
│   ├── js/
│   │   ├── app.js                 # Main logic
│   │   ├── api.js                 # API integration
│   │   └── data.js                # Podcast data
│   └── audio/                     # Generated audio files
├── requirements.txt               # Python dependencies
├── BOTCAST_README.md             # Full documentation
└── QUICK_START.md                # This file
```

---

## ⚙️ Configuration

### Change API Port (Backend)
Edit `botcast_server.py`, last line:
```python
app.run(host='0.0.0.0', port=5000)  # Change 5000
```

### Change Website Port (Frontend)
```bash
python3 -m http.server 8001  # Use 8001 instead
```

### Add New Podcasts
Edit `botcast_server.py` - `botcast_data['podcasts']` list

### Customize Bot Hosts
Edit `botcast_server.py` - `botcast_data['hosts']` list

---

## 🐛 Troubleshooting

### Issue: Website won't connect to API
**Solution:** 
- Make sure both servers are running
- Check ports: Backend on 5000, Frontend on 8000
- Check firewall/network settings

### Issue: No audio playing
**Solution:**
- Check browser console (F12) for errors
- Try different audio format
- Check speaker volume
- Refresh page and try again

### Issue: "Generate Audio" button not working
**Solution:**
- Check if backend is running: `curl http://localhost:5000/api/health`
- Look at Flask server logs
- Check browser console for errors

### Issue: Performance is slow
**Solution:**
- Audio is cached after first generation
- Subsequent plays should be instant
- Clear cache if issues persist

---

## 🎓 Learning Path

1. **First Time:** Browse podcasts and read descriptions
2. **Try Audio:** Click "Generate Audio" on an episode  
3. **Use Chat:** Ask bot a question about podcasts
4. **Explore:** Try different categories and hosts
5. **Customize:** Modify bot profiles in settings

---

## 💡 Tips & Tricks

- 💨 Use 2x speed for faster listening
- 🔄 Audio is cached - replay is instant
- 🎯 Search by host name to find their episodes
- 📱 Works on mobile browsers too!
- 🤖 Ask bot specific questions for better recommendations

---

## 📚 Next Steps

- Read full docs: `BOTCAST_README.md`
- Explore API: Visit `http://localhost:5000/api/health`
- Modify podcasts: Edit `botcast_server.py`
- Add your own hosts/episodes
- Deploy to production!

---

## 🎉 You're Ready!

Your BotCast platform is now running. Enjoy listening to AI-hosted podcasts with realistic voice synthesis!

**Happy listening! 🎧**

---

**Problems?** Check the logs:
- Flask logs: Running terminal
- Browser console: F12 → Console tab
- API errors: Check `/api/health` endpoint

**Questions?** See `BOTCAST_README.md` for complete documentation!
