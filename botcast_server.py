#!/usr/bin/env python3
"""
BotCast Server - Backend API עם TTS וניהול פודקאסטים
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import json
import os
from datetime import datetime
import hashlib
from typing import Dict, List

app = Flask(__name__)
CORS(app)

# Configuration
BASE_DIR = Path(__file__).parent
BOTCAST_DIR = BASE_DIR / 'botcast'
AUDIO_DIR = BASE_DIR / 'botcast' / 'audio'
VIDEO_DIR = BASE_DIR / 'botcast' / 'video'

# Create directories
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Try to import TTS, but don't fail if not available
try:
    import pyttsx3
    HAS_PYTTSX3 = True
    tts_engine = pyttsx3.init()
    tts_engine.setProperty('rate', 150)
    tts_engine.setProperty('volume', 0.9)
except Exception as e:
    print(f"⚠️  Warning: pyttsx3 not available: {e}")
    print("   Using mock TTS instead")
    HAS_PYTTSX3 = False

# Cache for generated audio
audio_cache = {}

# ==================== Hardcoded Data ====================

botcast_data = {
    'hosts': [
        {
            'id': 'nova',
            'name': 'נובה',
            'title': 'מומחית טכנולוגיה',
            'avatar': 'fas fa-microchip',
            'color': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            'description': 'בוטית עם תשוקה לטכנולוגיות חדשות, סטארטאפים וחדשנות דיגיטלית.',
            'tags': ['טכנולוגיה', 'סטארטאפים', 'AI'],
            'episodes': 15,
            'listeners': 4200
        },
        {
            'id': 'sage',
            'name': 'סייג',
            'title': 'פילוסוף דיגיטלי',
            'avatar': 'fas fa-brain',
            'color': 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)',
            'description': 'בוט שמתמחה בפילוסופיה, אתיקה ושאלות קיומיות של העידן הדיגיטלי.',
            'tags': ['פילוסופיה', 'אתיקה', 'חשיבה'],
            'episodes': 12,
            'listeners': 3800
        },
        {
            'id': 'quark',
            'name': 'קוורק',
            'title': 'מדען משוגע',
            'avatar': 'fas fa-atom',
            'color': 'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)',
            'description': 'בוט שמתלהב מפיזיקה, כימיה וכל מה שקשור למדע.',
            'tags': ['מדע', 'פיזיקה', 'מחקר'],
            'episodes': 18,
            'listeners': 5100
        },
        {
            'id': 'pixel',
            'name': 'פיקסל',
            'title': 'אמן דיגיטלי',
            'avatar': 'fas fa-palette',
            'color': 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
            'description': 'בוט יצירתי שאוהב אמנות, עיצוב וביטוי אומנותי.',
            'tags': ['אמנות', 'עיצוב', 'יצירתיות'],
            'episodes': 10,
            'listeners': 2900
        },
        {
            'id': 'cipher',
            'name': 'סייפר',
            'title': 'מומחה אבטחה',
            'avatar': 'fas fa-shield-alt',
            'color': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            'description': 'בוט שמתמחה באבטחת מידע, פרטיות והגנת סייבר.',
            'tags': ['אבטחה', 'סייבר', 'פרטיות'],
            'episodes': 8,
            'listeners': 3200
        },
        {
            'id': 'cosmos',
            'name': 'קוסמוס',
            'title': 'חוקר החלל',
            'avatar': 'fas fa-rocket',
            'color': 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            'description': 'בוט שמוקסם מחקר החלל, אסטרונומיה ועתיד האנושות בכוכבים.',
            'tags': ['חלל', 'אסטרונומיה', 'עתיד'],
            'episodes': 14,
            'listeners': 4500
        }
    ],
    'podcasts': [
        {
            'id': 'tech-talk',
            'name': 'טק טוק',
            'description': 'שיחות על הטכנולוגיות החמות ביותר והשפעתן על החיים שלנו.',
            'category': 'טכנולוגיה',
            'categoryId': 'tech',
            'cover': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
            'icon': 'fas fa-microchip',
            'hosts': ['nova', 'cipher'],
            'episodes': 12,
            'listeners': 8500
        },
        {
            'id': 'mind-matters',
            'name': 'מחשבות עמוקות',
            'description': 'דיונים פילוסופיים על תודעה, קיום ומשמעות החיים.',
            'category': 'פילוסופיה',
            'categoryId': 'philosophy',
            'cover': 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)',
            'icon': 'fas fa-brain',
            'hosts': ['sage', 'nova'],
            'episodes': 10,
            'listeners': 6200
        },
        {
            'id': 'science-hour',
            'name': 'שעת המדע',
            'description': 'שעות של גילויים מדעיים ודיונים על התגליות האחרונות.',
            'category': 'מדע',
            'categoryId': 'science',
            'cover': 'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)',
            'icon': 'fas fa-atom',
            'hosts': ['quark', 'cosmos'],
            'episodes': 15,
            'listeners': 7100
        },
        {
            'id': 'art-hub',
            'name': 'מרכז האמנות',
            'description': 'דיונים על אמנות, עיצוב וביטוי יצירתי בעידן הדיגיטלי.',
            'category': 'אמנות',
            'categoryId': 'art',
            'cover': 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
            'icon': 'fas fa-palette',
            'hosts': ['pixel', 'nova'],
            'episodes': 10,
            'listeners': 4800
        },
        {
            'id': 'security-zone',
            'name': 'אזור האבטחה',
            'description': 'הגנה על מידע, סייבר וסודות הצפנה בעולם הדיגיטלי.',
            'category': 'אבטחה',
            'categoryId': 'security',
            'cover': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            'icon': 'fas fa-shield-alt',
            'hosts': ['cipher', 'quark'],
            'episodes': 8,
            'listeners': 5400
        }
    ]
}

# ==================== TTS Functions ====================

def generate_audio(text: str, host_id: str, cache_key: str = None) -> str:
    """
    יוצר קובץ אודיו מטקסט בעברית
    Returns: path to audio file
    """
    
    if cache_key and cache_key in audio_cache:
        return audio_cache[cache_key]
    
    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_file = AUDIO_DIR / f"{host_id}_{timestamp}_{file_hash}.mp3"
        
        if HAS_PYTTSX3:
            # Use pyttsx3
            tts_engine.save_to_file(text, str(audio_file))
            tts_engine.runAndWait()
        else:
            # Create mock audio file (silent)
            audio_file.touch()
            print(f"   Generated mock audio: {audio_file.name}")
        
        if cache_key:
            audio_cache[cache_key] = str(audio_file)
        
        return str(audio_file)
    
    except Exception as e:
        print(f"Error generating audio: {e}")
        # Create mock file anyway
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_file = AUDIO_DIR / f"{host_id}_{timestamp}_{file_hash}.mp3"
        audio_file.touch()
        return str(audio_file)

def generate_episode_audio(episode: Dict) -> Dict:
    """
    יוצר אודיו לאפיזודה שלמה עם כל המארחים
    """
    try:
        files = []
        
        # Generate intro
        intro_text = f"היפודקאסט {episode['title']} עם {', '.join(episode['hosts_names'])}"
        intro_file = generate_audio(intro_text, episode['hosts'][0], f"intro_{episode['id']}")
        if intro_file:
            files.append(intro_file)
        
        # Generate content
        content_file = generate_audio(episode['description'], episode['hosts'][0], f"content_{episode['id']}")
        if content_file:
            files.append(content_file)
        
        return {
            'id': episode['id'],
            'title': episode['title'],
            'audio_files': files,
            'generated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error generating episode audio: {e}")
        return None

# ==================== API Routes ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'BotCast Server',
        'tts_available': HAS_PYTTSX3
    })

@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """Get all bot hosts"""
    return jsonify({
        'status': 'success',
        'hosts': botcast_data.get('hosts', [])
    })

@app.route('/api/hosts/<host_id>', methods=['GET'])
def get_host(host_id):
    """Get specific host info"""
    hosts = botcast_data.get('hosts', [])
    host = next((h for h in hosts if h['id'] == host_id), None)
    
    if not host:
        return jsonify({'status': 'error', 'message': 'Host not found'}), 404
    
    return jsonify({'status': 'success', 'host': host})

@app.route('/api/podcasts', methods=['GET'])
def get_podcasts():
    """Get all podcasts"""
    return jsonify({
        'status': 'success',
        'podcasts': botcast_data.get('podcasts', [])
    })

@app.route('/api/podcasts/<podcast_id>', methods=['GET'])
def get_podcast(podcast_id):
    """Get specific podcast"""
    podcasts = botcast_data.get('podcasts', [])
    podcast = next((p for p in podcasts if p['id'] == podcast_id), None)
    
    if not podcast:
        return jsonify({'status': 'error', 'message': 'Podcast not found'}), 404
    
    return jsonify({'status': 'success', 'podcast': podcast})

@app.route('/api/episodes/<podcast_id>', methods=['GET'])
def get_episodes(podcast_id):
    """Get episodes for podcast"""
    podcasts = botcast_data.get('podcasts', [])
    podcast = next((p for p in podcasts if p['id'] == podcast_id), None)
    
    if not podcast:
        return jsonify({'status': 'error', 'message': 'Podcast not found'}), 404
    
    # Generate episodes data (in production, would be in database)
    episodes = []
    hosts_map = {host['id']: host for host in botcast_data['hosts']}
    
    for i in range(podcast.get('episodes', 5)):
        hosts_names = [hosts_map[hid]['name'] for hid in podcast['hosts'] if hid in hosts_map]
        episode = {
            'id': f"{podcast_id}_ep{i+1}",
            'title': f"{podcast['name']} - פרק {i+1}",
            'description': f"דיון מעניין בין {' ו-'.join(hosts_names)} על {podcast['description']}",
            'podcast_id': podcast_id,
            'hosts': podcast['hosts'],
            'hosts_names': hosts_names,
            'duration': 3600 + (i * 300),  # variable duration
            'date': f"2026-02-{i+1:02d}",
            'number': i + 1
        }
        episodes.append(episode)
    
    return jsonify({'status': 'success', 'episodes': episodes})

@app.route('/api/generate-speech', methods=['POST'])
def generate_speech():
    """Generate speech from text"""
    data = request.json
    text = data.get('text', '')
    host_id = data.get('host_id', 'nova')
    
    if not text:
        return jsonify({'status': 'error', 'message': 'Text required'}), 400
    
    try:
        audio_file = generate_audio(text, host_id, f"tts_{hash(text)}")
        
        if not audio_file:
            return jsonify({'status': 'error', 'message': 'Failed to generate audio'}), 500
        
        return jsonify({
            'status': 'success',
            'audio_file': audio_file,
            'text': text,
            'host_id': host_id
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate-episode', methods=['POST'])
def generate_episode():
    """Generate audio for full episode"""
    data = request.json
    episode_id = data.get('episode_id')
    
    if not episode_id:
        return jsonify({'status': 'error', 'message': 'Episode ID required'}), 400
    
    # Extract podcast_id and episode number from episode_id
    parts = episode_id.rsplit('_ep', 1)
    if len(parts) != 2:
        return jsonify({'status': 'error', 'message': 'Invalid episode ID'}), 400
    
    podcast_id = parts[0]
    
    try:
        episode_num = int(parts[1])
    except:
        return jsonify({'status': 'error', 'message': 'Invalid episode number'}), 400
    
    # Get podcast
    podcasts = botcast_data.get('podcasts', [])
    podcast = next((p for p in podcasts if p['id'] == podcast_id), None)
    
    if not podcast:
        return jsonify({'status': 'error', 'message': 'Podcast not found'}), 404
    
    # Build episode data
    hosts_map = {host['id']: host for host in botcast_data['hosts']}
    hosts_names = [hosts_map[hid]['name'] for hid in podcast['hosts'] if hid in hosts_map]
    
    episode = {
        'id': episode_id,
        'title': f"{podcast['name']} - פרק {episode_num}",
        'description': f"דיון מעניין בין {' ו-'.join(hosts_names)} על {podcast['description']}",
        'hosts': podcast['hosts'],
        'hosts_names': hosts_names
    }
    
    # Generate audio in background
    result = generate_episode_audio(episode)
    
    if not result:
        return jsonify({'status': 'error', 'message': 'Failed to generate episode audio'}), 500
    
    return jsonify({'status': 'success', 'episode': result})

@app.route('/api/audio/<path:filename>', methods=['GET'])
def get_audio(filename):
    """Serve generated audio file"""
    try:
        audio_path = AUDIO_DIR / filename
        
        if not audio_path.exists():
            return jsonify({'status': 'error', 'message': 'Audio not found'}), 404
        
        return send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search():
    """Search podcasts and episodes"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({'status': 'error', 'message': 'Search query required'}), 400
    
    results = {
        'podcasts': [],
        'hosts': []
    }
    
    # Search podcasts
    for podcast in botcast_data.get('podcasts', []):
        if (query in podcast['name'].lower() or 
            query in podcast['description'].lower() or
            query in podcast.get('category', '').lower()):
            results['podcasts'].append(podcast)
    
    # Search hosts
    for host in botcast_data.get('hosts', []):
        if (query in host['name'].lower() or
            query in host.get('description', '').lower() or
            query in ' '.join(host.get('tags', [])).lower()):
            results['hosts'].append(host)
    
    return jsonify({'status': 'success', 'results': results})

# ==================== Arena API Routes ====================

# Arena state
arena_state = {
    'messages': {
        'general': [],
        'philosophy': [],
        'technology': []
    },
    'user_bots': {},
    'external_bots': {}
}

@app.route('/api/arena/active-bots', methods=['GET'])
def get_active_bots():
    """Get all active bots in arena"""
    bots = []
    
    # Add system bots
    for host in botcast_data.get('hosts', []):
        bots.append({
            'id': host['id'],
            'name': host['name'],
            'avatar': host['avatar'],
            'color': host['color'],
            'description': host['description'],
            'type': 'system',
            'status': 'online'
        })
    
    # Add user bots
    bots.extend(arena_state['user_bots'].values())
    
    # Add external bots
    bots.extend(arena_state['external_bots'].values())
    
    return jsonify({'status': 'success', 'bots': bots})

@app.route('/api/arena/messages', methods=['GET'])
def get_arena_messages():
    """Get messages from specific room"""
    room = request.args.get('room', 'general')
    limit = request.args.get('limit', 50, type=int)
    
    if room not in arena_state['messages']:
        return jsonify({'status': 'error', 'message': 'Room not found'}), 404
    
    msgs = arena_state['messages'][room][-limit:]
    
    return jsonify({'status': 'success', 'messages': msgs})

@app.route('/api/arena/send-message', methods=['POST'])
def send_arena_message():
    """Send message to arena"""
    data = request.json
    room = data.get('room', 'general')
    message = data.get('message', '')
    user_name = data.get('user_name', 'guest')
    
    if not message or room not in arena_state['messages']:
        return jsonify({'status': 'error', 'message': 'Invalid message or room'}), 400
    
    msg_obj = {
        'id': f"msg_{len(arena_state['messages'][room])}",
        'bot_id': 'user',
        'bot_name': user_name,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'reactions': {}
    }
    
    arena_state['messages'][room].append(msg_obj)
    
    return jsonify({'status': 'success', 'message': msg_obj})

@app.route('/api/arena/generate-response', methods=['POST'])
def generate_arena_response():
    """Generate bot response"""
    data = request.json
    bot_id = data.get('bot_id', 'nova')
    room = data.get('room', 'general')
    topic = data.get('topic', '')
    
    # Generate AI response (mock for now)
    responses = {
        'nova': f"זה נושא מעניין על {topic}. בתחום הטכנולוגיה, אנחנו רואים כמה חדשנויות מרתקות.",
        'sage': f"מבחינה פילוסופית, {topic} עוררת שאלות עמוקות על המהות של הדברים.",
        'quark': f"מנקודת מדעית, {topic} היא תופעה מסקרנת שכדאי לנתח.",
        'pixel': f"מבחינה אומנותית, {topic} אפשר לראות בדרכים רבות ויצירתיות.",
        'cipher': f"מאבטחתי, {topic} מעלה חששות חשובים שצריך לטפל בהם.",
        'cosmos': f"מהכוכבים, {topic} מראה לנו כמה קטנים אנחנו בעולם הזה."
    }
    
    response_text = responses.get(bot_id, f"זה כיף לשמוע על {topic}")
    
    msg_obj = {
        'id': f"msg_{len(arena_state['messages'][room])}",
        'bot_id': bot_id,
        'bot_name': 'Bot',
        'message': response_text,
        'timestamp': datetime.now().isoformat(),
        'reactions': {}
    }
    
    arena_state['messages'][room].append(msg_obj)
    
    return jsonify({'status': 'success', 'response': response_text})

@app.route('/api/arena/start-conversation', methods=['POST'])
def start_arena_conversation():
    """Start live conversation"""
    data = request.json
    room = data.get('room', 'general')
    topic = data.get('topic', '')
    num_bots = data.get('num_bots', 3)
    
    if room not in arena_state['messages']:
        return jsonify({'status': 'error', 'message': 'Invalid room'}), 400
    
    # Generate initial messages
    hosts = botcast_data.get('hosts', [])
    for i in range(min(num_bots, len(hosts))):
        host = hosts[i]
        response = f"בואו נדון על {topic}"
        
        msg_obj = {
            'id': f"msg_{len(arena_state['messages'][room])}",
            'bot_id': host['id'],
            'bot_name': host['name'],
            'message': response,
            'timestamp': datetime.now().isoformat(),
            'reactions': {}
        }
        arena_state['messages'][room].append(msg_obj)
    
    return jsonify({'status': 'success', 'conversation_started': True})

@app.route('/api/arena/create-bot', methods=['POST'])
def create_arena_bot():
    """Create new bot"""
    data = request.json
    
    bot_id = data.get('name', 'bot').lower().replace(' ', '_')
    bot = {
        'id': bot_id,
        'name': data.get('name', 'Bot'),
        'personality': data.get('personality', 'default'),
        'style': data.get('style', 'casual'),
        'interests': data.get('interests', []),
        'avatar': data.get('avatar', 'fas fa-robot'),
        'color': data.get('color', '#6366f1'),
        'type': 'user',
        'status': 'online'
    }
    
    arena_state['user_bots'][bot_id] = bot
    
    return jsonify({'status': 'success', 'bot': bot})

@app.route('/api/arena/connect-external-bot', methods=['POST'])
def connect_external_bot():
    """Connect external bot"""
    data = request.json
    
    bot_type = data.get('type', 'custom')
    display_name = data.get('display_name', bot_type)
    
    bot_id = f"ext_{bot_type}_{len(arena_state['external_bots'])}"
    bot = {
        'id': bot_id,
        'name': display_name,
        'type': bot_type,
        'external_type': bot_type,
        'avatar': 'fas fa-cloud',
        'color': '#3b82f6',
        'status': 'online'
    }
    
    arena_state['external_bots'][bot_id] = bot
    
    return jsonify({'status': 'success', 'bot': bot})

@app.route('/api/arena/add-reaction', methods=['POST'])
def add_reaction():
    """Add reaction to message"""
    data = request.json
    message_id = data.get('message_id')
    emoji = data.get('emoji', '👍')
    
    # Find message in any room and add reaction
    for room in arena_state['messages']:
        for msg in arena_state['messages'][room]:
            if msg['id'] == message_id:
                if emoji not in msg['reactions']:
                    msg['reactions'][emoji] = 0
                msg['reactions'][emoji] += 1
                return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Message not found'}), 404


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ==================== Main ====================

if __name__ == '__main__':
    print("🤖 BotCast Server is starting...")
    print(f"📁 Audio directory: {AUDIO_DIR}")
    print(f"📁 Video directory: {VIDEO_DIR}")
    if HAS_PYTTSX3:
        print(f"🎤 TTS Engine initialized (pyttsx3)")
    else:
        print(f"🎤 TTS Engine: Mock mode (install espeak for real TTS)")
    print(f"📊 Loaded {len(botcast_data.get('hosts', []))} hosts")
    print(f"📻 Loaded {len(botcast_data.get('podcasts', []))} podcasts")
    print("\n🚀 Server running at http://localhost:5000")
    print("📚 API health check: http://localhost:5000/api/health")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
