# 🚨 EchoGuard v2.0 - AI Crisis Detection System

**AI-powered emergency response system using multimodal search for rapid crisis detection**
EchoGuard is an AI agent designed for first responders and disaster management teams. It doesn't just search; it remembers how a crisis evolves by correlating ground-level photos, emergency audio transcripts, and satellite data.

> Intelligent analysis of crisis images + descriptions to find similar past incidents and provide emergency protocols

## 🎯 What is EchoGuard?

EchoGuard is an emergency response AI system that helps detect and analyze natural disasters in real-time. Upload an image of a flood, fire, or earthquake, describe what you see, and get instant access to similar past incidents with proven response protocols.

**How it works in 30 seconds:**
1. Upload crisis image (flood, fire, earthquake, etc.)
2. Describe the situation
3. AI searches 25 real crisis cases
4. Get top 3 similar incidents + similarity scores
5. Access emergency action protocols + save to knowledge base

## ✨ Key Features

### 🔍 Multimodal Analysis
- Analyze **both images AND text descriptions** simultaneously
- 60% image intelligence + 40% text intelligence = hybrid search
- Find relevant past crises in seconds

### 📊 25 Real Crisis Database
- **5 Flood cases**: Mumbai, Assam, Gujarat, Bangalore, Kolkata
- **5 Fire cases**: Delhi, Mumbai, Bangalore, Hyderabad, Chennai
- **5 Earthquake cases**: Gujarat, Kashmir, Himachal, Maharashtra, Uttarakhand
- **5 Landslide cases**: Himachal, Uttarakhand, Kerala, Meghalaya, Arunachal Pradesh
- **5 Cyclone cases**: Chennai, Odisha, Gujarat, Andaman, West Bengal

### 🚨 Emergency Protocols
- 5-step action plans for each crisis type
- Based on real disaster response best practices
- Instant access during emergencies

### 💾 Continuous Learning
- Save new incidents to vector database
- Future searches will find your new cases
- System grows smarter with every analysis

### ⚡ Lightning Fast
- Results in <5 seconds
- 70-95% similarity accuracy
- Cloud-ready architecture

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   FRONTEND (Streamlit - 4 tabs)     │
├─────────────────────────────────────┤
│ • Analyze Crisis                    │
│ • View Database                     │
│ • Past Incidents                    │
│ • Info & Documentation              │
├─────────────────────────────────────┤
│   AI ENGINE (OpenAI CLIP)           │
│ • 512-dim embeddings                │
│ • Image + Text encoders             │
├─────────────────────────────────────┤
│   DATABASE (Qdrant Vector DB)       │
│ • 25 pre-loaded crises              │
│ • User uploads (continuous learning)│
│ • Cosine similarity search          │
└─────────────────────────────────────┘
```

**Tech Stack:**
- Frontend: Streamlit
- AI Model: OpenAI CLIP (multimodal)
- Vector DB: Qdrant
- Backend: Python 3.8+
- Deployment: Streamlit Cloud / Docker

## 🚀 Quick Start

### Local Setup (5 Minutes)

**Prerequisites:**
- Python 3.8+
- Docker (for Qdrant)
- 4GB RAM

**Installation:**
```bash
# Clone repo
git clone https://github.com/sourabhtripathi0614-san/Echoguard
cd echoguard

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
```

**Run Application:**
```bash
# Terminal 1: Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:latest

# Terminal 2: Launch app
streamlit run app_fixed.py
```

Open: http://localhost:8501

### Option 3: Docker
```bash
docker build -t echoguard .
docker run -p 8501:8501 echoguard
```

## 📖 How to Use

### Tab 1: Analyze Crisis (Main Feature)
```
1. Upload image → Select flood/fire/earthquake photo
2. Describe crisis → Type what you see
3. Click Analyze → AI searches (2-5 seconds)
4. View results → Top 3 similar incidents + scores
5. Save to memory → Stores as new case (optional)
```

### Tab 2: View Database
- See all 25 pre-loaded crisis cases
- Grouped by type
- Full metadata: location, casualties, damage
- Click for emergency protocols

### Tab 3: Past Incidents
- Filter by crisis type
- Search historical cases
- View incident timeline
- Compare similar events

### Tab 4: Info & Documentation
- System instructions
- Feature overview
- Results interpretation
- Help documentation

## 🔧 Configuration

### Environment Variables (.env)
```
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
DEVICE=cpu
OPENAI_API_KEY=sk-proj-...
```

### For Qdrant Cloud (Production)
```
QDRANT_URL=https://your-cluster.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DEVICE=cpu
```

## 📊 Database Schema

Each crisis case includes:
```json
{
  "id": "flood_001",
  "type": "flood",
  "location": "Mumbai, Maharashtra, India",
  "description": "Heavy rainfall led to severe flooding...",
  "timestamp": "2024-05-26 14:00",
  "severity": "critical",
  "affected_people": 5000,
  "casualties": 12,
  "damage_estimate": "₹500 crores",
  "response_time": "2 hours",
  "emergency_actions": [
    "Evacuate low-lying areas immediately",
    "Activate rescue boats and teams",
    "Setup emergency shelters",
    "Distribute food and water supplies",
    "Coordinate with local hospitals"
  ]
}
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Search Speed | 2-5 sec (CPU) / <1 sec (GPU) |
| Accuracy | 70-95% (cosine distance) |
| Database | 25 incidents + uploads |
| Embedding | 512-dim (CLIP) |
| Memory | ~2GB (local) |
| Users | Unlimited (cloud) |

## 🚀 Deployment

### Streamlit Cloud (Recommended - FREE)
```
1. Push code to GitHub
2. Go to share.streamlit.io
3. Sign in with GitHub
4. Deploy in 2 clicks
```

## 🔒 Security

✅ API keys in environment variables (not in code)
✅ .env file in .gitignore (never committed)
✅ Streamlit Secrets for cloud
✅ No permanent user data storage
✅ HTTPS by default on Streamlit Cloud
✅ Input validation on uploads

## 📁 Project Files

```
echoguard/
├── app_fixed.py              # Main Streamlit app
├── config_fixed.py           # 25 crisis cases
├── qdrant_service_fixed.py   # Vector DB ops
├── clip_service.py           # Embeddings
├── memory_service.py         # User uploads
├── requirements.txt          # Dependencies
├── .env.example              # Template
├── .gitignore                # Git config
├── README.md                 # This file
├── DEPLOYMENT_GUIDE.md       # Deploy steps
└── LICENSE                   # MIT License
```

## 🎓 Learn From This Project

- Multimodal AI (vision + language)
- Vector databases & similarity search
- Streamlit web apps
- API integration
- Production deployment
- Docker containerization
- Emergency response systems

## 🤝 Contributing

Found a bug? Create an issue.
Have ideas? Fork and submit a PR.
Like it? Star the repo! ⭐

```bash
git checkout -b feature/your-feature
# Make changes
git commit -am "Add feature"
git push origin feature/your-feature
# Create Pull Request
```


## 📄 License

MIT License - Use freely with attribution

## 🎉 Credits

Built with:
- **OpenAI CLIP** - Multimodal embeddings
- **Qdrant** - Vector database
- **Streamlit** - Web framework
- **Python** - Programming language

Inspired by disaster response needs in India.

