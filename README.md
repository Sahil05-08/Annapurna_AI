# 🍛 Annapurna AI - Agentic Cooking Assistant

An intelligent, AI-powered cooking assistant that generates personalized recipes, plans meals, detects ingredients from fridge photos, and provides voice guidance—all powered by advanced LLMs and agentic reasoning.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Gradio](https://img.shields.io/badge/Gradio-Web%20UI-orange)
![Groq](https://img.shields.io/badge/Groq-LLM%20API-green)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Memory-purple)
![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face-yellow)

---

## 🚀 **LIVE DEMO - Try It Now!**

### ⭐ **Click below to use Annapurna AI right now (No installation needed!)**

### 🔗 **[Annapurna AI - Live on Hugging Face Spaces](https://huggingface.co/spaces/Sahil585/Annapurna_AI)**

Just click the link above and start asking for recipes! 🍛

---

## 🌟 **What You Can Do (Live Demo):**

✅ **Ask for any recipe** - "Chicken Biryani recipe", "Paneer Butter Masala kaise banaye"
✅ **Tell ingredients** - "I have egg and bread"
✅ **Upload fridge photos** - 📸 AI detects ingredients automatically
✅ **Voice input** - 🎙️ Speak ingredients or recipe names
✅ **Meal planning** - 📅 Generate 3-7 day meal plans
✅ **Listen to recipes** - 🔊 Audio recipe playback
✅ **Get nutrition info** - 📊 Calories, protein, carbs, fat
✅ **Multi-language support** - 🌍 English, Hindi, Marathi

---

## ✨ Features

### 🍳 **Direct Recipe Generation**
- Ask for any Indian recipe by name—no ingredients needed!
- Examples: "Chicken Biryani recipe", "Paneer Butter Masala kaise banaye"
- Complete recipes with ingredients, step-by-step instructions, cooking time, pro tips

### 🥘 **Ingredient-Based Recipe Creation**
- Tell me what ingredients you have → Get customized recipes
- Multi-language support: English, Hindi, Marathi
- Smart ingredient detection with fuzzy matching

### 📸 **Fridge Vision Detection**
- Upload a photo of your fridge/kitchen
- AI automatically detects all visible ingredients
- Works best with clear, well-lit photos

### 📅 **Intelligent Meal Planning**
- Generate 3-7 day meal plans with breakfast, lunch, dinner
- Considers available ingredients and preferences
- Reduces cooking decision fatigue

### 🎙️ **Voice Input & Audio Recipes**
- Speak ingredients or recipe names
- Groq Whisper API for speech-to-text
- Listen to recipes with text-to-speech (edge-tts)

### 🌍 **Multi-Language Support**
- English, Hindi (Hinglish), Marathi
- Bad word detection in 3 languages with respectful responses
- Flexible input normalization for casual speech

### 📊 **Nutrition Calculator**
- Per-serving nutritional information (calories, protein, carbs, fat)
- Database of 50+ common Indian ingredients
- Health-conscious recipe adjustments

### 🛒 **Shopping List Generator**
- Extract ingredients with quantities from recipes
- Organized by ingredient type
- Pantry essentials checklist

### 💾 **Persistent Memory (ChromaDB)**
- Remembers user preferences over time
- Learns dietary restrictions and favorite cuisines
- Personalizes recipe suggestions

### 🤖 **Agentic Reasoning Loop**
- Dynamic tool selection (search database, generate recipe, ask clarification)
- Smart fallback mechanisms
- Multi-attempt verification with quality checks

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | Gradio 4.x |
| **LLM API** | Groq (`llama-3.3-70b-versatile`) |
| **Vision/Audio** | Groq API (Whisper, Vision models) |
| **Vector Database** | ChromaDB (Persistent) |
| **Text-to-Speech** | edge-tts |
| **Image Processing** | Pillow (PIL) |
| **Fuzzy Matching** | rapidfuzz |
| **Web Search** | Tavily API |
| **Configuration** | python-dotenv |
| **Deployment** | Hugging Face Spaces |

---

## 📋 Prerequisites (For Local Installation)

- **Python 3.8+**
- **API Keys:**
  - Groq API key (free tier available)
  - Tavily API key (for web recipe search)
- **System Requirements:**
  - 500MB disk space (ChromaDB)
  - 2GB RAM minimum
  - Internet connection

---

## 🚀 Installation (Local Setup)

### 1. Clone/Download Repository
```bash
git clone https://github.com/Sahil05-08/Annapurna_AI.git
cd Annapurna_AI
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

**Get API Keys:**
- **Groq:** https://console.groq.com (free tier: $5 free credits)
- **Tavily:** https://tavily.com (free tier available)

### 5. Prepare Data
Create `data/recipes.json` with recipe data:

```json
[
  {
    "recipe_name": "Paneer Butter Masala",
    "ingredients": ["paneer", "tomato", "cream", "butter", "garlic", "ginger"],
    "instructions": "...",
    "difficulty": "medium",
    "time_minutes": 25
  }
]
```

### 6. Run the Application
```bash
python app.py
```

The app will launch at `http://localhost:7860`

---

## 📖 Usage Guide

### **Method 1: Direct Recipe Request**
Simply ask for any recipe:
```
"Chicken Biryani recipe"
"How to make Paneer Butter Masala"
"Dal Makhani kaise banaye"
```

### **Method 2: Type Ingredients**
Tell the AI what you have:
```
"I have paneer, tomato, onion"
"potato and spinach only"
"egg and bread, make it quick"
```

Add preferences:
```
"Make it spicy" 🌶️
"I want something healthy" 🥗
"Quick recipe under 15 mins" ⚡
```

### **Method 3: Voice Input**
1. Click "Tap to speak"
2. Say ingredients or recipe name
3. Click "Send Voice"

### **Method 4: Fridge Photo**
1. Go to "📸 Fridge Scan" tab
2. Upload a clear fridge photo
3. AI detects ingredients automatically
4. Use detected ingredients for recipe

### **Method 5: Meal Planning**
1. Go to "📅 Meal Planner" tab
2. Enter ingredients (comma-separated)
3. Select number of days (3-7)
4. Choose preference (healthy/spicy/quick/vegan/balanced)
5. Get full meal plan

---

## 📁 Project Structure

```
Annapurna_AI/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .env.example             # Setup template
├── app.py                    # Main application file
├── data/
│   └── recipes.json          # Recipe database
├── memory_store/             # ChromaDB persistent storage (auto-created)
└── .gitignore               # Git ignore file
```

---

## 🧠 How It Works

### **Agent Architecture**

```
User Input
    ↓
Bad Word Detection (Block inappropriate content)
    ↓
Input Normalization (Handle casual speech, typos)
    ↓
Spell Correction (Fuzzy match against ingredient list)
    ↓
Intent Detection (greeting/recipe/chat/closing)
    ↓
State Management (Track ingredients, preferences, servings)
    ↓
Agent Reasoning Loop:
    ├─ Tool Selection (database search / generate / clarify)
    ├─ Tool Execution (Execute selected tool)
    ├─ Result Verification (Quality & completeness check)
    └─ Fallback (If verification fails, retry with different approach)
    ↓
Output Formatting:
    ├─ Recipe generation
    ├─ Step-by-step instructions
    ├─ Nutrition calculation
    ├─ Audio generation
    └─ Shopping list
    ↓
User Response
```

### **Key Components**

| Component | Function |
|-----------|----------|
| **Bad Word Detector** | Scans for inappropriate language across 3 languages |
| **Normalizer** | Converts casual speech, slang, Hindi mixing → clean English |
| **Spell Checker** | Fuzzy-matches user ingredients against 100+ known items |
| **Intent Classifier** | Determines if user wants greeting, recipe, chat, or closing |
| **State Manager** | Tracks ingredients, preferences, servings, conversation history |
| **Agent Controller** | Selects best tool based on current situation |
| **Tool Suite** | Database search, AI generation, clarification, web search |
| **Verifier** | Ensures output meets quality standards (word count, structure) |
| **Formatter** | Adds nutrition, audio, shopping list, cooking time |

---

## 🎯 Supported Recipes

### Indian Cuisines
- **North Indian:** Biryani, Pulao, Dal Makhani, Butter Chicken
- **South Indian:** Dosa, Idli, Sambar, Rasam, Uttapam
- **Curries:** Paneer Butter Masala, Egg Curry, Fish Curry, Mutton Curry
- **Breads:** Naan, Roti, Paratha, Puri, Bhature
- **Street Food:** Pav Bhaji, Chole Bhature, Samosa

### Recipe Customization
- 🌶️ **Spicy** - Add extra chili, bold spices
- 🥗 **Healthy** - Low oil, steaming, nutrient-rich
- ⚡ **Quick** - Under 20 minutes, minimal steps
- 🌱 **Vegan** - No dairy, no ghee, oil-based
- 💪 **Protein** - High protein, muscle-building

---

## 🔒 Safety Features

### **Bad Word Detection**
- Multi-language support (English, Hindi, Marathi)
- Respectful, funny punch-line responses
- Encourages positive interaction
- Examples of detected phrases:
  - English: "damn", "fuck", "bullshit"
  - Hindi: "chutiya", "bhenchod", "gali"
  - Marathi: "gaali", "madarchod", "gava"

### **Content Filtering**
- Blocks harmful or offensive input
- Returns encouraging messages
- No user data stored without consent

---

## ⚙️ Configuration

### **Environment Variables (.env)**
```env
# Required
GROQ_API_KEY=gsk_xxxx...              # Groq API key
TAVILY_API_KEY=tvly_xxxx...           # Tavily search API key

# Optional
CHROMADB_PATH=./memory_store          # Vector DB location
MAX_RECIPE_LENGTH=1200                # Max tokens for recipe
MAX_ATTEMPTS=3                        # Agent retry attempts
DEFAULT_SERVINGS=2                    # Default serving size
```

### **Customization Options**

Edit these in `app.py`:

```python
# Adjust nutrition database
NUTRITION_DB = { ... }

# Modify ingredient detection
KNOWN_INGREDIENTS = [ ... ]

# Change bad word dictionary
BAD_WORDS = { ... }

# Update preference prompts
PREFERENCE_PROMPTS = { ... }

# Cooking time estimates
INGREDIENT_COOK_TIME = { ... }
```

---

## 🚨 Troubleshooting

### **Issue: "No API key provided"**
- Check `.env` file exists in project root
- Verify `GROQ_API_KEY` is set correctly
- Test: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GROQ_API_KEY'))"`

### **Issue: Image detection not working**
- Ensure image is clear and well-lit
- Try cropping to show only ingredients
- Check Groq API quota
- Verify vision model is available in your region

### **Issue: Slow recipe generation**
- Groq API might be rate-limited
- Reduce `max_tokens` in API calls
- Increase `temperature` for faster inference
- Check internet connection

### **Issue: ChromaDB permission errors**
- Ensure write permissions in project directory
- Delete `memory_store/` and restart (fresh DB)
- Check available disk space

### **Issue: Audio not playing**
- Check browser audio permissions
- Verify edge-tts is installed: `pip install edge-tts`
- Clear browser cache and reload
- Try different browser

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Average Response Time** | 3-8 seconds |
| **Recipe Generation** | 4-6 seconds |
| **Image Detection** | 3-5 seconds |
| **Voice Transcription** | 1-3 seconds |
| **Meal Plan Generation** | 6-10 seconds |
| **Memory Queries** | < 500ms |

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add more recipe databases
- [ ] Expand language support (Tamil, Telugu, Kannada)
- [ ] Mobile app version
- [ ] Database integration (MongoDB, PostgreSQL)
- [ ] User authentication & profiles
- [ ] Calorie tracking over time
- [ ] Dietary restriction presets
- [ ] Export recipes to PDF

**To contribute:**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is open source. Created by **Sahil Suryawanshi**.

---

## 👨‍💻 Author

**Sahil Suryawanshi**
- 🔗 LinkedIn: [linkedin.com/in/sahil585](https://www.linkedin.com/in/sahil585/)
- 📧 Email: suryawanshisahil585@gmail.com
- 🐙 GitHub: [github.com/Sahil05-08](https://github.com/Sahil05-08)
- 🤗 Hugging Face: [huggingface.co/Sahil585](https://huggingface.co/Sahil585)

---

## 🙏 Acknowledgments

- **Groq** - Free LLM API with amazing speed
- **Gradio** - Beautiful web UI framework
- **Hugging Face Spaces** - Free deployment platform
- **ChromaDB** - Vector database for memory
- **edge-tts** - Text-to-speech synthesis
- **rapidfuzz** - Fuzzy string matching
- **Tavily** - Web search integration

---

## 🍛 What's Next?

### **Roadmap**
- [ ] **v2.0** - Multi-user profiles with recipe history
- [ ] **v2.1** - Restaurant recipe database integration
- [ ] **v2.2** - Real-time kitchen timer & notifications
- [ ] **v2.3** - Social recipe sharing & ratings
- [ ] **v3.0** - Mobile app (React Native)
- [ ] **v3.1** - Smart grocery list with prices
- [ ] **v3.2** - Budget meal planning feature

---

## 💡 Quick Tips

✅ **For Best Results:**
- Use clear, specific recipe names (not just "curry")
- Mention preferences upfront (spicy/healthy/quick)
- Upload well-lit fridge photos
- Speak clearly for voice input
- Check nutrition info for balanced meals

⚠️ **Limitations:**
- Requires internet connection
- Depends on API availability
- Not a substitute for professional nutritionists
- Recipe accuracy depends on ingredient quality
- Some niche ingredients may not be recognized

---

## 📞 Support

For issues, questions, or feature requests:
1. Check this README first
2. Review the "How to Use" tab in the app
3. Check troubleshooting section above
4. Contact: suryawanshisahil585@gmail.com

---

## 🎯 Links

| Resource | Link |
|----------|------|
| **Live Demo** | 🔗 [Hugging Face Spaces](https://huggingface.co/spaces/Sahil585/Annapurna_AI) |
| **GitHub** | 🔗 [GitHub Repository](https://github.com/Sahil05-08/Annapurna_AI) |
| **LinkedIn** | 🔗 [Sahil Suryawanshi](https://www.linkedin.com/in/sahil585/) |
| **Hugging Face** | 🔗 [Profile](https://huggingface.co/Sahil585) |

---

**Happy Cooking!** 🍛👨‍🍳

*Made with ❤️ for food lovers everywhere*

---

**Last Updated:** April 2026
**Version:** 1.1.0
**Status:** ✅ Live on Hugging Face Spaces
