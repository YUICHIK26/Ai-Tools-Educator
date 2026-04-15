# 🎓 AI Tools Educator

A comprehensive AI-powered educational platform that teaches users about various AI tools across 60 different categories, from writing and coding to design and content creation.

## 👥 Contributors & Partners

This project is developed and maintained by:

- **[YUICHIK26](https://github.com/YUICHIK26)** - Project Creator & Lead Developer
- **[KashifAnsarix7](https://github.com/KashifAnsarix7)** - Partner, Developer & Designer

We welcome contributions from the community! If you'd like to contribute, please refer to [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🌟 Features

### Core Features
- **Interactive AI Chatbot** - Conversational AI that recommends tools and provides guidance
- **Smart Tool Recommendations** - Get AI tool suggestions based on your specific needs
- **60+ AI Tool Categories** - Curated content covering:
  - Writing & Content Creation
  - Image & Video Generation
  - Coding & Development
  - Design & Creative Tools
  - Business & Productivity
  - And many more...

### Advanced Features
- **Real-time Search** - Stay updated with the latest AI tools and news
- **Screen Analysis** - AI-powered screen understanding and context
- **Automation** - Automate repetitive tasks with AI
- **Audio Processing** - Text-to-speech and speech recognition
- **System Controls** - Voice or text-based brightness, volume control
- **Teaching Agent** - Educational guidance with explanations
- **Multi-Chat Support** - Manage multiple conversations simultaneously

### AI Model Integration
- **Cohere** - Decision-making and text generation
- **Groq** - Fast LLM inference for chatbot responses
- **ElevenLabs** - High-quality text-to-speech
- **Firebase** - Authentication and data storage
- **Google Search Integration** - Real-time information retrieval

## 📋 Prerequisites

Before you begin, make sure you have:
- **Python 3.10.11** or higher
- **pip** (Python package manager)
- **Git** (for version control)
- API keys from:
  - Cohere (https://cohere.ai/)
  - Groq (https://groq.com/)
  - ElevenLabs (https://elevenlabs.io/)
  - Firebase (https://firebase.google.com/)

## 🚀 Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/YUICHIK26/Ai-Tools-Educator.git
cd Ai-Tools-Educator
```

### Step 2: Setup Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r Requirements.txt
```

### Step 4: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Open .env in your text editor and fill in:
# - CohereAPIKey
# - GroqAPIKey
# - ElevenLabsAPIKey
# - Firebase credentials
```

### Step 5: Run the Application
```bash
# Navigate to the app directory
cd app

# Run the Flask server
python app.py

# The application will be available at: http://localhost:5000
```

## 📝 Configuration

### Environment Variables (.env)

Create a `.env` file in the project root with the following variables:

```env
# User Configuration
Username=Your Name

# Cohere API (for AI routing and decision-making)
CohereAPIKey=YOUR_COHERE_API_KEY

# Groq API (for fast chatbot responses)
GroqAPIKey=YOUR_GROQ_API_KEY

# ElevenLabs API (for voice generation)
ElevenLabsAPIKey=YOUR_ELEVENLABS_API_KEY

# Firebase Configuration (for authentication)
FirebaseAPIKey=YOUR_FIREBASE_API_KEY
FirebaseAuthDomain=YOUR_FIREBASE_AUTH_DOMAIN
FirebaseProjectId=YOUR_FIREBASE_PROJECT_ID
FirebaseStorageBucket=YOUR_FIREBASE_STORAGE_BUCKET
FirebaseMessagingSenderId=YOUR_FIREBASE_MESSAGING_SENDER_ID
FirebaseAppId=YOUR_FIREBASE_APP_ID
```

See `.env.example` for all available configuration options.

### Getting API Keys

#### Cohere API Key
1. Visit https://dashboard.cohere.com/
2. Sign up or log in
3. Go to API keys section
4. Create a new API key
5. Copy and paste into `.env`

#### Groq API Key
1. Visit https://console.groq.com/
2. Sign up or log in
3. Navigate to API keys
4. Create a new key
5. Copy and paste into `.env`

#### ElevenLabs API Key
1. Go to https://elevenlabs.io/
2. Create an account
3. Access your API key from the profile section
4. Copy and paste into `.env`

#### Firebase Setup
1. Go to https://console.firebase.google.com/
2. Create a new project
3. Enable Authentication (Email/Password)
4. Enable Firestore Database
5. Copy the SDK configuration values to `.env`

## 🎯 Usage

### Starting the Web Application
```bash
cd app
python app.py
```

Access the application at `http://localhost:5000`

### Main Features to Try

1. **Dashboard** - Overview of all available AI tools
2. **Chat** - Interactive AI chatbot for recommendations
3. **Features** - Detailed information about supported features
4. **About** - Project information and credits
5. **Contact** - Support and feedback

### Example Queries to Try

- "What AI tools can help me with content writing?"
- "Show me video generation tools"
- "Which AI tool is best for code debugging?"
- "Recommend an AI design tool"
- "Tell me about AI chatbots"

## 🏗️ Project Structure

```
Ai-Tools-Educator/
├── app/
│   ├── app.py                 # Main Flask application
│   ├── Backend/
│   │   ├── Model.py           # Decision-making model with Cohere
│   │   ├── Chatbot.py         # Groq-powered conversational AI
│   │   ├── TextToSpeech.py    # ElevenLabs integration
│   │   ├── Automation.py      # Task automation
│   │   ├── ScreenAnalysis.py  # Screen understanding
│   │   ├── SystemControls.py  # Brightness/volume control
│   │   └── [other modules]
│   ├── static/                # CSS, JavaScript, static assets
│   ├── templates/             # HTML templates
│   └── data/                  # Data files and databases
├── Data/                      # User data, conversations, uploads
├── Tutorial Videos/           # Educational video content
├── Front-end/                 # Frontend resources
├── Requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Actual environment variables (NOT in git)
└── README.md                 # This file
```

## 🔐 Security & Privacy

⚠️ **Important Security Notes:**

1. **Never commit `.env` file** - Keep your API keys private
2. **Use `.env.example`** - Share this template instead of actual credentials
3. **Rotate API keys regularly** - Update keys every few months
4. **Never share your keys** - Don't commit them to GitHub or share in messages

The `.env` file is added to `.gitignore` and will not be tracked by git.

## 📦 Requirements

See `Requirements.txt` for the complete list of dependencies. Key packages include:

- **Flask** - Web framework
- **Cohere** - AI model routing
- **Groq** - Fast LLM inference
- **ElevenLabs** - Text-to-speech
- **Firebase** - Authentication and database
- **Beautiful Soup** - Web scraping
- **OpenCV** - Computer vision
- **PyQt5** - GUI components
- And 70+ other dependencies

## 🐛 Troubleshooting

### Issue: "No module named 'flask'"
**Solution:** Ensure you've activated the virtual environment and run `pip install -r Requirements.txt`

### Issue: "API key not found"
**Solution:** Check that your `.env` file exists in the project root with all required API keys

### Issue: "GROQ_API_KEY is not set"
**Solution:** Make sure `GroqAPIKey=YOUR_KEY` is properly set in `.env`

### Issue: Firebase initialization error
**Solution:** Verify your Firebase credentials in the `.env` file and check that authentication is enabled in Firebase Console

### Issue: Python version incompatibility
**Solution:** Ensure you're using Python 3.10.11 or higher: `python --version`

## 🤝 Contributing

Contributions are welcome! Please feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 💬 Support & Contact

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in the `/Tutorial Videos` folder
- Visit the About page in the web application


## �🙏 Acknowledgments

Special thanks to all the AI tool creators and API providers that make this platform possible:
- Cohere for AI decision-making
- Groq for fast LLM inference
- ElevenLabs for text-to-speech
- Google for search integration
- Firebase for authentication and database

## 📚 Learning Resources

This platform includes 60+ tutorial categories covering:
- AI Writing Generation
- AI Chatbots
- AI Image Generation
- AI Coding Assistants
- AI Voice Cloning
- And many more...

Explore the `/Tutorial Videos` directory for detailed educational content.

---

**Happy Learning! 🚀**

For the latest updates and features, visit the GitHub repository:
https://github.com/YUICHIK26/Ai-Tools-Educator
