import json
import os
import re
import asyncio
import tempfile
import base64
import string
import gradio as gr
from rapidfuzz import process
from groq import Groq
from dotenv import load_dotenv
import chromadb
from datetime import datetime
import edge_tts
from PIL import Image
from tavily import TavilyClient


# ==============================
# 🔑 GROQ CLIENT
# ==============================
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

import random

# Bad words dictionary in multiple languages
BAD_WORDS = {
        # ENGLISH (Fixed - word boundary safe)
    "english": [
    # Single words
    "damn", "hell", "crap", "bastard", "asshole",
    "fuck", "shit", "bitch", "bullshit", "horseshit",
    "cunt", "piss", "f*ck", "sh*t", "b*tch", "d*mn", "h*ll",
    "chutiya", "gaali",
    
    # Multi-word phrases
    "mother fucker", "motherfucker", "mother f*cker",
    "son of a bitch", "son of bitch",
    "fuck you", "fuck off", "go fuck",
    "shit ass", "shit head", "shit face",
    "f*ck you", "sh*t ass"
  ],

    
    # HINDI / HINGLISH
    "hindi": [
        "gaali", "gali", "saleya", "bhenchod", "mc", "bc", "chutiya",
        "bakwaas", "harami", "badmash", "nalayak", "bewakoof", "kamina",
        "kutta", "suar", "saala", "gadha", "ullu", "chakka",
        "maa ka", "baap ka", "behen ka", "bhaiya ka", "nikal", "gand",
        "lavda", "lauda", "tatte", "thoos", "jhoot", "chump",
        "jahil", "pagal", "randi"
    ],
    
    # MARATHI
    "marathi": [
        "gaali", "gali", "gaunchya", "madarchod", "behenchod", "chutiya",
        "gava", "gadha", "bakri", "kutta", "suar", "sali", "saali",
        "bewakoof", "murkh", "don", "doni", "maza",
        "bapa ka", "aai ka", "bhen ka", "bhau ka", "maher", "gand",
        "jhut", "burwa", "nalayak"
    ]
}

# Respectful/Funny punch line responses
PUNCH_LINES = {
    "english": [
        "🙏 Hey! I'm here to help with recipes, not bad words! Let's keep it respectful, okay?",
        "😊 That language won't cook a meal! How about we focus on making something delicious instead?",
        "🍽️ I only understand the language of food, my friend! Bad words don't make recipes taste better!",
        "🚫 Whoa there! Even angry people need to eat healthy. Let's make a nice dish instead!",
        "😌 Your words hurt, but your hunger matters! Let's find you a great recipe!",
        "🧘 I'm here to spread positivity, not negativity! Bad vibes won't help us cook!",
        "💫 Remember: A happy kitchen makes happy food. Let's be kind to each other!",
        "🙌 Come on, we're better than this! Tell me what ingredients you have, not bad words!"
    ],
    
    "hindi": [
        "🙏 भैया/बहन! मैं गाली सुनने के लिए यहाँ नहीं हूँ! आइए रेसिपी बनाते हैं! 🍛",
        "😊 गाली से खाना नहीं बनता! आइए कुछ स्वादिष्ट बनाते हैं! 😋",
        "🍽️ मैं तो खाने की भाषा समझता हूँ! गाली में कोई स्वाद नहीं है! 😄",
        "🚫 अरे! गुस्से में भी खाना तो खाना ही है! कुछ अच्छा बनाते हैं न! 👨‍🍳",
        "😌 शब्दों से चोट लगती है, पर भूख असली है! एक अच्छी रेसिपी बनाते हैं! 💪",
        "🧘 मैं सकारात्मकता फैलाता हूँ, नकारात्मकता नहीं! आइए मिल-बैठकर खाना बनाएँ! ✨",
        "💫 खुश रसोई = खुशी का खाना! आइए एक-दूसरे के साथ अच्छा व्यवहार करें! 🙌",
        "🙌 अरे, हम इससे बेहतर हैं! अपनी सामग्री बताइए, गाली नहीं! 😊"
    ],
    
    "marathi": [
        "🙏 भाऊ/बहिण! मला गाली ऐकायला येत नाही! आपण रेसिपी बनवूया! 🍛",
        "😊 गाली मारून खाना बनत नाही! कोणती स्वादिष्ट चीज बनवायची? 😋",
        "🍽️ मी खाण्याची भाषा समजतो! गालीत कोणताही स्वाद नाही! 😄",
        "🚫 अरे! गुस्सात आहात तर काय, तरी खाणं पडणे आहे! काहीतरी बनवूया! 👨‍🍳",
        "😌 शब्दांनी दुःख होते, पण भूख सत्य आहे! एक अच्छी रेसिपी बनवूया! 💪",
        "🧘 मी सकारात्मकता देतो, नकारात्मकता नाही! आपण मला मदत करूया! ✨",
        "💫 खुश स्वयंपाक = खुशीचा खाना! आपण एकमेकांचे सन्मान करूया! 🙌",
        "🙌 अरे, आपण याहून चांगले आहात! सामग्री सांगा, गाली नाही! 😊"
    ]
}

def detect_bad_words(text):
    """
    Detect bad words with proper handling for single & multi-word phrases
    Returns: (has_bad_words: bool, language: str)
    """
    try:
        text_lower = text.lower().strip()
        
        # Check each language
        for language, bad_words_list in BAD_WORDS.items():
            for bad_word in bad_words_list:
                # ✅ FIX: Handle single vs multi-word phrases differently
                if ' ' not in bad_word:
                    # Single word: use word boundaries
                    pattern = r'\b' + re.escape(bad_word) + r'\b'
                else:
                    # Multi-word phrase: split, escape each word, rejoin with flexible spacing
                    words = bad_word.split()
                    pattern = r'\b' + r'\s+'.join(re.escape(w) for w in words) + r'\b'
                
                # Search for the pattern
                if re.search(pattern, text_lower):
                    print(f"[BadWords] ⛔ Detected {language} bad word: '{bad_word}'")
                    return True, language
        
        print(f"[BadWords] ✅ No bad words detected")
        return False, None
    
    except Exception as e:
        print(f"[BadWords] Error in detection: {e}")
        return False, None

def get_punch_line(language):
    """
    Get a random respectful/funny punch line in the detected language
    """
    try:
        if language and language in PUNCH_LINES:
            punch_line = random.choice(PUNCH_LINES[language])
            print(f"[BadWords] 🎯 Punch line in {language}")
            return punch_line
        else:
            # Fallback to English if language not found
            return random.choice(PUNCH_LINES["english"])
    
    except Exception as e:
        print(f"[BadWords] Error getting punch line: {e}")
        return "🙏 Let's keep our conversation respectful! 😊"

# ==============================
# 🧠 PERSISTENT MEMORY (ChromaDB)
# ==============================
# ✅ Persistent ChromaDB - saves to disk
chroma_client = chromadb.PersistentClient(path="./memory_store")
memory_db = chroma_client.get_or_create_collection("user_memory")

def save_memory(user_id, info):
    """Save user preference/info permanently"""
    try:
        memory_db.add(
            documents=[info],
            ids=[f"{user_id}_{datetime.now().timestamp()}"]
        )
        print(f"[Memory] Saved: {info}")
    except Exception as e:
        print(f"[Memory] Save error: {e}")

def get_memory(user_id, query):
    """Recall relevant memories for this user"""
    try:
        results = memory_db.query(
            query_texts=[query],
            n_results=3
        )
        memories = results['documents'][0] if results['documents'] else []
        return memories
    except Exception as e:
        print(f"[Memory] Recall error: {e}")
        return []

# ==============================
# 📂 LOAD DATA
# ==============================
with open("data/recipes.json", "r") as f:
    recipes = json.load(f)

KNOWN_INGREDIENTS = [
    # Vegetables
    "tomato","onion","potato","spinach","carrot","peas","cabbage","cauliflower",
    "broccoli","lettuce","cucumber","zucchini","eggplant","capsicum","beetroot",
    "corn","pumpkin","radish","sweet potato","spring onion","leek","asparagus",
    "artichoke","okra","turnip","celery","kale","arugula",

    # Fruits
    "apple","banana","orange","mango","grapes","strawberry","pineapple","papaya",
    "watermelon","pear","peach","plum","kiwi","pomegranate","avocado","blueberry",
    "raspberry","blackberry","coconut","lime","lemon",

    # Indian staples
    "rice","wheat","atta","maida","besan","rava","poha","dal","lentil","chickpea",
    "rajma","moong dal","toor dal","urad dal","chana dal",

    # Dairy
    "milk","butter","ghee","cream","cheese","paneer","yogurt","curd","buttermilk",

    # Protein / Non-veg
    "egg","chicken","mutton","fish","shrimp","prawn","crab","turkey","beef","pork",

    # Plant proteins
    "tofu","soybean","soya chunks","tempeh","kidney beans","black beans",

    # Spices (Indian + global)
    "salt","sugar","black pepper","white pepper","turmeric","cumin","coriander",
    "garam masala","red chili powder","paprika","oregano","thyme","rosemary",
    "basil","bay leaf","clove","cardamom","cinnamon","nutmeg","mustard seeds",
    "fennel seeds","fenugreek","asafoetida","star anise","saffron",

    # Oils & sauces
    "oil","olive oil","mustard oil","coconut oil","soy sauce","vinegar",
    "balsamic vinegar","fish sauce","oyster sauce","hot sauce","ketchup",
    "mayonnaise","mustard sauce","barbecue sauce","salsa","pesto",

    # Grains & carbs
    "bread","pasta","noodles","quinoa","oats","barley","millet","tortilla",

    # Nuts & seeds
    "almond","cashew","walnut","peanut","pistachio","chia seeds","flax seeds",
    "sunflower seeds","pumpkin seeds","sesame seeds",

    # Herbs
    "coriander leaves","mint","parsley","dill","chives","basil leaves",

    # Mexican / Continental extras
    "jalapeno","chipotle","nacho","taco shell","refried beans","guacamole",
    "sour cream","cheddar cheese","mozzarella","parmesan",

    # Misc
    "honey","chocolate","cocoa","vanilla","yeast","baking powder","baking soda"
]

# ==============================
# 🥗 NUTRITION CALCULATOR
# ==============================
NUTRITION_DB = {
    # Vegetables
    "tomato": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2},
    "onion": {"calories": 40, "protein": 1.1, "carbs": 9, "fat": 0.1},
    "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1},
    "spinach": {"calories": 23, "protein": 2.7, "carbs": 3.6, "fat": 0.4},
    "carrot": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2},
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4},
    "cabbage": {"calories": 25, "protein": 1.3, "carbs": 6, "fat": 0.1},
    "cauliflower": {"calories": 25, "protein": 1.9, "carbs": 5, "fat": 0.3},
    "capsicum": {"calories": 31, "protein": 1, "carbs": 6, "fat": 0.3},
    "mushroom": {"calories": 22, "protein": 3.1, "carbs": 3.3, "fat": 0.3},

    # Fruits
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    "orange": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1},
    "mango": {"calories": 60, "protein": 0.8, "carbs": 15, "fat": 0.4},
    "avocado": {"calories": 160, "protein": 2, "carbs": 9, "fat": 15},

    # Indian staples
    "rice": {"calories": 206, "protein": 4.3, "carbs": 45, "fat": 0.3},
    "wheat": {"calories": 340, "protein": 13, "carbs": 72, "fat": 2.5},
    "dal": {"calories": 120, "protein": 9, "carbs": 20, "fat": 0.4},
    "chickpea": {"calories": 164, "protein": 9, "carbs": 27, "fat": 2.6},
    "rajma": {"calories": 127, "protein": 8.7, "carbs": 23, "fat": 0.5},

    # Dairy
    "milk": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3},
    "paneer": {"calories": 265, "protein": 18, "carbs": 1.2, "fat": 21},
    "cheese": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33},
    "butter": {"calories": 717, "protein": 0.9, "carbs": 0.1, "fat": 81},
    "yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.4},
    "cream": {"calories": 340, "protein": 2.2, "carbs": 2.8, "fat": 35},

    # Protein (Non-veg)
    "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11},
    "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6},
    "fish": {"calories": 206, "protein": 22, "carbs": 0, "fat": 12},
    "shrimp": {"calories": 99, "protein": 24, "carbs": 0.2, "fat": 0.3},

    # Plant protein
    "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8},
    "soybean": {"calories": 173, "protein": 16.6, "carbs": 9.9, "fat": 9},

    # Grains / carbs
    "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.3},
    "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1},
    "oats": {"calories": 389, "protein": 17, "carbs": 66, "fat": 7},

    # Oils & extras
    "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100},
    "sugar": {"calories": 387, "protein": 0, "carbs": 100, "fat": 0},
    "honey": {"calories": 304, "protein": 0.3, "carbs": 82, "fat": 0},

    # Herbs / spices (low calories but added)
    "ginger": {"calories": 80, "protein": 1.8, "carbs": 18, "fat": 0.8},
    "garlic": {"calories": 149, "protein": 6.4, "carbs": 33, "fat": 0.5}
}

def calculate_nutrition(ingredients, servings=2):
    try:
        total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
        for ingredient in ingredients:
            if ingredient.lower() in NUTRITION_DB:
                n = NUTRITION_DB[ingredient.lower()]
                for key in total:
                    total[key] += n[key]
        if servings > 0:
            for key in total:
                total[key] = round(total[key] / servings, 1)
        return f"""
🥗 **Nutrition Info (per serving):**
- 🔥 Calories: {total['calories']} kcal
- 💪 Protein: {total['protein']}g
- 🌾 Carbs: {total['carbs']}g
- 🧈 Fat: {total['fat']}g
"""
    except Exception as e:
        return ""

def calculate_nutrition_for_recipe(recipe_text):
    """Extract nutrition info from recipe text or provide default tips"""
    try:
        if "biryani" in recipe_text.lower():
            return """
🥗 **Nutritional Note:**
- Protein-rich from chicken/paneer
- Carbs from basmati rice
- 💡 For healthier version: use brown rice and less oil

⚖️ **Portion guide:** 1 plate = ~400-500 calories
"""
        elif "paneer" in recipe_text.lower():
            return """
🥗 **Nutritional Note:**
- Rich in protein and calcium
- Good source of healthy fats
- 💡 For lighter version: use low-fat paneer

⚖️ **Portion guide:** 1 serving = ~350-400 calories
"""
        elif "dal" in recipe_text.lower() or "daal" in recipe_text.lower():
            return """
🥗 **Nutritional Note:**
- Excellent plant-based protein
- High in fiber
- 💡 Pairs perfectly with rice or roti

⚖️ **Portion guide:** 1 bowl = ~200-250 calories
"""
        else:
            return """
💡 **Nutrition Tip:**
For accurate nutrition info, tell me your specific ingredients!
Say "I have [ingredients]" and I'll calculate exact nutrition. 📊
"""
    except:
        return ""
    
# ==============================
# ⏱️ COOKING TIME & DIFFICULTY
# ==============================
INGREDIENT_COOK_TIME = {
    "tomato": 10, "onion": 5, "potato": 15, "paneer": 5,
    "egg": 5, "rice": 20, "dal": 30, "spinach": 5,
    "carrot": 10, "mushroom": 8, "chicken": 25,
    "ginger": 2, "garlic": 2, "lemon": 0, "bread": 0, "milk": 0
}

def get_cooking_metrics(ingredients):
    try:
        max_time = max(
            (INGREDIENT_COOK_TIME.get(i.lower(), 5) for i in ingredients),
            default=5
        ) + 5

        if len(ingredients) <= 2:
            difficulty = "⭐ Easy"
        elif len(ingredients) <= 4:
            difficulty = "⭐⭐ Medium"
        else:
            difficulty = "⭐⭐⭐ Hard"

        return f"""
⏱️ **Cooking Metrics:**
- {difficulty}
- ⏱️ Estimated Time: {max_time} minutes
"""
    except Exception as e:
        return ""

# ==============================
# 🛒 SHOPPING LIST GENERATOR
# ==============================
def generate_shopping_list(recipe_text):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Extract ingredients with quantities from recipe. Format as bullet list only."
                },
                {
                    "role": "user",
                    "content": f"Extract ingredients from:\n{recipe_text}"
                }
            ],
            max_tokens=200,
            temperature=0.1
        )
        shopping = response.choices[0].message.content
        return f"""
🛒 **Shopping List:**
{shopping}
💡 Check pantry for salt, oil, water
"""
    except Exception as e:
        return ""
    
# ==============================
# 🔊 TEXT TO SPEECH (edge-tts)
# ==============================
# Converts Recipie text to speech and returns HTML audio player with base64 encoded audio
def text_to_speech(text):
    try:
        clean = text.replace('**','').replace('#','')
        clean = ''.join(c for c in clean if ord(c) < 128)
        clean = clean[:500]

        async def generate():
            communicate = edge_tts.Communicate(clean, voice="en-IN-NeerjaNeural")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                return f.name

        path = asyncio.run(generate())

        with open(path, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode()

        return f"""
<div style='background:rgba(245,200,66,0.08);
            border:0.5px solid rgba(245,200,66,0.2);
            border-radius:12px; padding:14px; margin-top:10px;'>
    <p style='color:#e8a06a; font-size:12px; margin:0 0 8px;
              text-transform:uppercase; letter-spacing:2px;'>🔊 LISTEN TO RECIPE</p>
    <audio controls style='width:100%; filter:sepia(0.3)'>
        <source src='data:audio/mp3;base64,{audio_data}' type='audio/mp3'>
    </audio>
</div>"""

    except Exception as e:
        print(f"[TTS] Error: {e}")
        return ""
     
def detect_ingredients_from_image(image_path):
    """Detect ingredients from fridge photo"""
    try:
        if image_path is None:
            print("[Vision] ❌ No image path provided")
            return None

        # Resize image to save tokens
        img = Image.open(image_path)
        img = img.convert("RGB")  # ✅ Fix: ensure RGB (no alpha channel issues)
        img.thumbnail((512, 512))

        # ✅ Fix: use tempfile properly instead of hardcoded /tmp path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            temp_path = tmp.name
            img.save(temp_path, format="JPEG")

        with open(temp_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()

        print(f"[Vision] Image encoded, size: {len(img_data)} chars")

        # ✅ Fix: use the latest available Groq vision model
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # ✅ updated model
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """Look at this fridge/kitchen photo carefully.
List ONLY the food ingredients you can clearly see.
Format your answer EXACTLY like this: ingredient1, ingredient2, ingredient3
Maximum 8 ingredients. Just the comma-separated list, nothing else."""
                    }
                ]
            }],
            max_tokens=150
        )

        detected = response.choices[0].message.content.strip()

        # ✅ Fix: clean up any extra text the model might add
        # Keep only the first line if model returns multiple lines
        detected = detected.strip(string.punctuation)

        # Remove common prefixes the model sometimes adds
        for prefix in ["I can see:", "Ingredients:", "I see:", "The ingredients are:"]:
            if detected.lower().startswith(prefix.lower()):
                detected = detected[len(prefix):].strip()

        print(f"[Vision] ✅ Detected: {detected}")

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        return detected if detected else None

    except Exception as e:
        print(f"[Vision] ❌ Error: {type(e).__name__}: {e}")
        return None

def transcribe_audio(audio_path):
    """Transcribe voice input using Groq Whisper API"""
    if audio_path is None:
        return ""
    try:
        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                language="en",   # works for Hindi/Marathi too
                response_format="text"
            )
        result = transcription.strip()
        print(f"[Voice] Transcribed: {result}")
        return result
    except Exception as e:
        print(f"[Voice] Error: {e}")
        return ""

def handle_image_upload(image_path, history):
    """Handle fridge image and auto-fill ingredients"""
    if image_path is None:
        return history, ""

    history.append({
        "role": "user",
        "content": "📸 [Uploaded fridge photo]"
    })

    detected = detect_ingredients_from_image(image_path)

    if detected:
        reply = f"""📸 **I can see these ingredients in your fridge:**

{detected}

Shall I suggest a recipe using these? Just say **"yes make recipe"** or add more ingredients!"""
    else:
        reply = "Couldn't detect ingredients clearly. Please type them manually! 😊"

    history.append({"role": "assistant", "content": reply})
    return history, detected

# ==============================
# 🧠 SESSION MEMORY
# ==============================
user_state = {}

def get_user_state(user_id):
    if user_id not in user_state:
        user_state[user_id] = {
            "ingredients": [],
            "preference": None,
            "last_recipe": None,
            "attempt": 0,
            "servings": 2
        }
    return user_state[user_id]

# ==============================
# 🎯 NORMALIZE INPUT (NEW - FLEXIBLE)
# ==============================
def normalize_user_input(text):
    """
    Super-flexible input normalization.
    Handles: slang, broken English, missing words, casual speech, Hindi mixing
    """
    text = text.lower().strip()
    
    # Remove common filler words & casual speech
    fillers = [
        r"\b(uh|umm|err|like|basically|kind\s+of|sort\s+of|you\s+know|right|okay|alright|hmm)\b",
        r"\b(please|pls|thanks|thank\s+you|buddy|bro|man|dude)\b"
    ]
    for filler_pattern in fillers:
        text = re.sub(filler_pattern, "", text, flags=re.IGNORECASE)
    
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    # Convert common slang/casual English
    slang_map = {
        r"\bu\b": "you",
        r"\bur\b": "your",
        r"\bu\s+r\b": "you are",
        r"\bu r\b": "you are",
        r"\bdont\b": "don't",
        r"\bdoesnt\b": "doesn't",
        r"\bwanna\b": "want to",
        r"\bgonna\b": "going to",
        r"\bgotta\b": "got to",
        r"\bcant\b": "can't",
        r"\bcould\s+nt\b": "couldn't",
        r"\bwouldnt\b": "wouldn't",
        r"\bshoudnt\b": "shouldn't",
        r"\bn\b": "and",  # "tomato n onion"
        r"\bw\b": "with",  # "paneer w garlic"
        r"\bk\b": "with",  # "paneer k sath" (hindi)
    }
    
    for slang_pattern, proper in slang_map.items():
        text = re.sub(slang_pattern, proper, text, flags=re.IGNORECASE)
    
    # Convert common Hindi food words to English
    hindi_to_english = {
        r"\b(aloo|alu)\b": "potato",
        r"\b(pyaaz|piaz)\b": "onion",
        r"\b(adrak|adrakh)\b": "ginger",
        r"\b(lahsun|lahsan)\b": "garlic",
        r"\b(tamatar|tamata)\b": "tomato",
        r"\b(palak|paalak)\b": "spinach",
        r"\b(khumbhi|mushroom)\b": "mushroom",
        r"\b(mutter|peas)\b": "peas",
        r"\b(basmati|chawal)\b": "rice",
        r"\b(masala)\b": "spice",
        r"\b(nok\s*salt|namak)\b": "salt",
        r"\b(tel|oil)\b": "oil",
    }
    
    for hindi_pattern, english in hindi_to_english.items():
        text = re.sub(hindi_pattern, english, text, flags=re.IGNORECASE)
    
    # Remove punctuation except apostrophes in contractions
    text = re.sub(r"[.,!?;:\-—_/\\|~`@#$%^&*()+=\[\]{}\"<>]+", "", text)
    
    # Final space cleanup
    text = re.sub(r"\s+", " ", text).strip()
    
    print(f"[Normalize] Input: {text}")
    return text

# ==============================
# 🔤 SPELLING CORRECTION
# ==============================
def fix_spelling(text):
    """Correct spelling using fuzzy matching"""
    words = text.lower().split()
    corrected = []
    
    # Skip very short words to avoid wrong matches
    skip_words = [
        "hi", "hey", "i", "a", "an", "the", "have", 
        "has", "had", "and", "or", "but", "not", "only",
        "just", "want", "make", "me", "my", "is", "it",
        "to", "in", "on", "at", "of", "for", "with",
        "hello", "namaste", "please", "can", "you", "get",
        "do", "does", "did", "will", "would", "should"
    ]
    
    for word in words:
        if word in skip_words:
            corrected.append(word)
            continue
        if len(word) <= 2:
            corrected.append(word)
            continue
        
        # Fuzzy match against known ingredients
        match = process.extractOne(word, KNOWN_INGREDIENTS, score_cutoff=80)
        if match:
            corrected.append(match[0])
            if match[0] != word:
                print(f"[Spelling] Corrected: {word} → {match[0]}")
        else:
            corrected.append(word)
    
    result = " ".join(corrected)
    print(f"[Spelling] After: {result}")
    return result
def detect_servings(text):
    """
    Extract serving count from user message.
    Handles: "for 4 people", "serves 2", "4 log", "3 janon ke liye", "4 jano sathi"
    Returns: int (default 2)
    """
    patterns = [
        r'for\s+(\d+)\s*(people|persons?|members?|adults?|kids?|guests?)',
        r'serves?\s+(\d+)',
        r'(\d+)\s*(people|persons?|members?|log|jano|janon)',
        r'(\d+)\s*(ke\s+liye|ke\s+liye|sathi|saathi|maate)',  # Hindi/Marathi
        r'(\d+)\s+servings?',
        r'feed\s+(\d+)',
        r'family\s+of\s+(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            n = int(match.group(1))
            n = max(1, min(n, 20))  # clamp between 1 and 20
            print(f"[Servings] Detected: {n}")
            return n
    return 2  # default
# ==============================
# 🎯 INTENT DETECTION
# ==============================
def detect_intent(text):
    """Detect user intent from message"""
    text = text.lower()
    
    if any(g in text for g in ["hi", "hello", "hey", "namaste", "greet"]):
        return "greeting"
    if any(w in text for w in KNOWN_INGREDIENTS):
        return "recipe"
    if any(w in text for w in ["thank", "thanks", "bye", "goodbye", "see you", "goodbye"]):
        return "closing"
    return "chat"

# ==============================
# 🧠 UPDATE STATE
# ==============================
def update_state(user_id, message):
    """Extract ingredients and preferences from user message"""
    state = get_user_state(user_id)
    text = message.lower()

    # ✅ FIX: Reset if user says "I have X" with a fresh statement (not "also" or "and")
    fresh_start_patterns = [
        r"^i have\s", r"^i only have\s", r"^only have\s",
        r"^i just have\s", r"^i got\s", r"^i've got\s"
    ]
    additive_keywords = ["also", "and also", "plus", "add", "too", "as well", "moreover"]
    
    is_fresh_start = any(re.search(p, text) for p in fresh_start_patterns)
    is_additive = any(kw in text for kw in additive_keywords)

    # Reset ingredients if user is making a fresh statement (not adding)
    if is_fresh_start and not is_additive:
        state["ingredients"] = []
        print("[State] ✅ Fresh ingredient statement → resetting ingredients list")

    # Existing reset for "only/just"
    reset_keywords = ["only", "just", "i have only", "i only have", "only have"]
    if any(keyword in text for keyword in reset_keywords):
        state["ingredients"] = []
        print("[State] ✅ Ingredients reset due to 'only/just'")

    skip_words = [
        "hi", "hey", "i", "a", "an", "the", "have",
        "has", "and", "or", "but", "not", "only",
        "just", "want", "make", "me", "my", "is", "it",
        "hello", "namaste", "please", "can", "you", "get",
        "to", "in", "on", "at", "of", "for", "with",
        "do", "does", "did", "will", "would", "should",
        "also", "add", "too", "plus", "also", "got"
    ]

    for word in text.split():
        if word in skip_words:
            continue
        if len(word) <= 2:
            continue
        match = process.extractOne(word, KNOWN_INGREDIENTS, score_cutoff=80)
        if match:
            ing = match[0]
            if ing not in state["ingredients"]:
                state["ingredients"].append(ing)
                print(f"[State] ➕ Added ingredient: {ing}")

    # Preference detection (unchanged)
    preference_keywords = {
        "healthy": ["healthy", "light", "fit", "diet", "low", "health"],
        "spicy": ["spicy", "hot", "chilli", "chili", "masala", "tandoori"],
        "protein": ["protein", "strong", "muscle"],
        "vegan": ["vegan", "vegetarian", "veggie", "no meat", "no dairy"],
        "quick": ["quick", "fast", "hurry", "5 min", "10 min"]
    }
    for pref, keywords in preference_keywords.items():
        if any(k in text for k in keywords):
            state["preference"] = pref
            print(f"[State] 📌 Preference: {pref}")
            save_memory(user_id, f"User prefers {pref} food")
            break

    servings = detect_servings(message)
    state["servings"] = servings

    print(f"[State] Final → ingredients={state['ingredients']}, preference={state['preference']}, servings={state['servings']}")
    return state

# ==============================
# 🔍 TOOL 1: SEARCH DATABASE
# ==============================
def search_database(user_ingredients):
    """Search local recipe database for matching recipes"""
    if not recipes:
        print("[DB Tool] ❌ No recipes loaded")
        return None
    
    best_match = None
    max_match = 0
    
    for recipe in recipes:
        recipe_ingredients = [i.lower() for i in recipe.get("ingredients", [])]
        match_count = len(set(user_ingredients) & set(recipe_ingredients))
        
        if match_count > max_match:
            max_match = match_count
            best_match = recipe

    if best_match and max_match > 0:
        recipe_name = best_match.get('recipe_name', 'Unknown')
        print(f"[DB Tool] ✅ Found: {recipe_name} (matched {max_match} ingredients)")
        return best_match
    
    print("[DB Tool] ❌ No matching recipe found")
    return None

# ==============================
# 🌐 TOOL 2: GENERATE WITH AI
# ==============================
PREFERENCE_PROMPTS = {
    "spicy":   "Make it very spicy with bold heat. Use red chillies, black pepper, and fiery spice levels.",
    "healthy": "Make it healthy, low-oil, and nutrient-rich. Prefer steaming or light sautéing. Avoid heavy fats.",
    "quick":   "Make it quick and easy, under 20 minutes. Minimal steps, one-pan if possible.",
    "vegan":   "Make it strictly vegan. No dairy, no ghee, no honey. Use oil instead of butter.",
    "protein": "Make it high-protein. Maximize protein content and suggest protein-boosting pantry additions.",
}

def generate_with_ai(ingredients, preference=None, base_recipe=None, memories=None, servings=2):
    if not ingredients:
        return "❌ No ingredients provided. Please tell me what you have!"

    base_info = f"Base recipe found: {base_recipe.get('recipe_name')}\n" if base_recipe else "Creating from scratch.\n"
    memory_context = "\n".join(memories[:2]) if memories else "No previous preferences"

    preference_instruction = PREFERENCE_PROMPTS.get(
        preference.lower() if preference else "",
        preference or "no specific preference"
    )

    # ✅ Only basic seasoning is ever allowed — no free pantry additions
    BASIC_SEASONING = "salt, oil, water, and basic dry spices (cumin, turmeric, black pepper, red chili, coriander powder, garam masala)"

    prompt = f"""You are Annapurna, an expert Indian cooking assistant making delicious recipes.
User's ingredients: {', '.join(ingredients)}
User preference: {preference_instruction}
{base_info}
User's past preferences: {memory_context}

🎯 YOUR TASK: Make the BEST possible recipe using ONLY the user's ingredients!

✅ STRICT RULES:
1. MUST USE: {', '.join(ingredients)}
2. You may ONLY add: {BASIC_SEASONING}
3. ⛔ DO NOT add any other vegetables, proteins, dairy, or ingredients the user has NOT mentioned.
   For example: if the user did NOT mention onion, tomato, paneer, garlic — do NOT include them.
4. STRICTLY FOLLOW preference: {preference_instruction}
5. Be friendly and conversational

📋 FORMAT:
🍛 **Dish Name**
One line description

🧂 **Ingredients:**
- {(chr(10) + '- ').join(ingredients)}
- Salt, oil (basic cooking)
[Only spices from the allowed list above — no extra vegetables or proteins]

📝 **Steps:**
1. ...
2. ...
3. ...

⏱️ **Cooking Time:** X minutes
💡 **Pro Tip:** One helpful tip
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Annapurna, a friendly expert Indian cooking assistant.

CRITICAL RULES — follow without exception:
1. The user has these ingredients: {', '.join(ingredients)}
2. Build the ENTIRE recipe using ONLY these ingredients.
3. You may ONLY add: {BASIC_SEASONING}
4. ⛔ NEVER add ingredients the user did not mention — not onion, not tomato, not garlic, not paneer, nothing extra.
5. If an ingredient seems missing, work creatively with what is provided.
6. The user wants a {preference or 'standard'} style dish: {preference_instruction}"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600,
            temperature=0.3
        )

        result = response.choices[0].message.content
        print(f"[AI Tool] ✅ Generated strict recipe for: {ingredients}")
        return result

    except Exception as e:
        print(f"[AI Tool] ❌ Groq Error: {e}")
        return None

def generate_specific_dish_with_ingredients(dish_name, ingredients, preference=None):
    """Generate a specific dish using available ingredients"""
    prompt = f"""You are Annapurna, an expert Indian cooking assistant.
User wants to make: {dish_name}
User has these ingredients: {', '.join(ingredients)}
Preference: {preference or 'standard'}

Make the BEST possible {dish_name} using ONLY these ingredients.
If some traditional ingredients are missing, suggest creative substitutes using what they have.

FORMAT:
🍛 **{dish_name.title()}** (Modified for available ingredients)

🧂 **Ingredients Used:**
- {(chr(10) + '- ').join(ingredients)}
- Basic pantry: salt, oil, spices

📝 **Instructions:**
1. ...
2. ...
(Continue with detailed steps)

⏱️ **Time:** X minutes
💡 **Substitutions Used:** [Explain what you substituted and why]

Serve hot! 🍽️"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert Indian chef. Create practical recipes using available ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Specific Dish] Error: {e}")
        return None

# ==============================
# ❓ TOOL 3: ASK CLARIFICATION
# ==============================
def ask_clarification(state):
    """Ask user for more information"""
    if not state["ingredients"]:
        return """😊 I'd love to help! Tell me:
- What ingredients do you have?
- Any preferences? (healthy/spicy/quick/vegan)

Example: "I have paneer and tomato, make it spicy"
or "I only have potato and onion"
"""
    
    if not state["preference"]:
        return f"""Great! You have: {', '.join(state['ingredients'])}

Now tell me your preference:
- 🌶️ Spicy
- 🥗 Healthy
- ⚡ Quick
- 🌱 Vegan
- 💪 Protein-rich
"""
    
    return "Tell me more about what you'd like! 😊"

# ==============================
# ✅ TOOL 4: VERIFY RESULT
# ==============================
def verify_result(output, ingredients):
    if not output:
        print("[Verify] ❌ No output")
        return False
    
    if len(output) < 50:
        print("[Verify] ❌ Too short")
        return False
    
    if len(output.split()) < 20:
        print("[Verify] ❌ Less than 20 words")
        return False
    
    # ✅ Check ingredients appear
    found_count = sum(1 for ing in ingredients 
                     if ing.lower() in output.lower())
    
    # ✅ FOR SINGLE INGREDIENT: Skip exact match check if recipe has steps
    if len(ingredients) == 1:
        has_steps = any(word in output.lower() 
                       for word in ["step", "cook", "add", "heat", "mix", "serve", "fry", "boil", "prepare"])
        if has_steps:  # If recipe has cooking instructions, approve it
            print(f"[Verify] ✅ Valid: Single ingredient recipe with steps")
            return True
    
    # ✅ For multiple ingredients, check if at least one appears
    if found_count == 0:
        print("[Verify] ❌ No ingredients found")
        return False
    
    # ✅ Check recipe has basic structure
    has_steps = any(word in output.lower() 
                   for word in ["step", "cook", "add", "heat", "mix", "serve"])
    if not has_steps:
        print("[Verify] ❌ No cooking instructions found")
        return False
    
    print(f"[Verify] ✅ Valid: {found_count} ingredients, has steps")
    return True

# ==============================
# 🛠️ TOOL 5: ADJUST RECIPE
# ==============================
def adjust_recipe(text, preference):
    """Add preference-based tips to recipe"""
    tips = {
        "spicy": "\n🌶️ **Pro Tip:** Add extra green chilli or red chilli powder for more heat!",
        "healthy": "\n🥗 **Pro Tip:** Use less oil and serve with fresh salad.",
        "protein": "\n💪 **Pro Tip:** Add an egg or extra paneer for more protein!",
        "vegan": "\n🌱 **Pro Tip:** Use coconut milk instead of cream. Skip paneer.",
        "quick": "\n⚡ **Pro Tip:** Use a pressure cooker or microwave to save time!"
    }
    
    if preference and preference in tips:
        return text + tips[preference]
    return text

# ==============================
# ⭐ RECIPE RATING
# ==============================
def save_rating(user_id, rating):
    state = get_user_state(user_id)
    last = state.get("last_recipe", "Unknown recipe")
    save_memory(user_id, f"Rated {rating}/5 stars: {last[:60]}")
    return f"Thanks! Saved {rating}⭐ rating!"

# ==============================
# 👨‍🍳 STEP MODE
# ==============================
def generate_step_mode(recipe_text):
    try:
        lines = recipe_text.split('\n')
        steps = [l for l in lines if l.strip() and l.strip()[0].isdigit() and '.' in l]
        if not steps:
            return ""
        steps_html = ""
        for i, step in enumerate(steps, 1):
            steps_html += f"""
<div style='background:rgba(245,200,66,0.08);
            border:0.5px solid rgba(245,200,66,0.2);
            border-radius:10px; padding:12px; margin:6px 0;'>
    <span style='color:#f5c842; font-weight:bold;'>Step {i}</span>
    <p style='color:#f5e6c8; margin:4px 0 0;'>{step.strip()}</p>
</div>"""
        return f"""
<div style='margin-top:12px;'>
    <p style='color:#e8a06a; font-size:12px; text-transform:uppercase;
              letter-spacing:2px;'>👨‍🍳 COOKING STEPS</p>
    {steps_html}
</div>"""
    except:
        return ""

# ==============================
# 🌐 WEB RECIPE SEARCH
# ==============================
def search_web_recipes(ingredients, preference=None):
    try:
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        query = f"Indian recipe with {', '.join(ingredients[:3])}"
        if preference:
            query += f" {preference}"
        query += " easy homemade"
        results = tavily.search(query=query, max_results=3, search_depth="basic")
        if not results.get('results'):
            return None
        output = "🌐 **Found Online Recipes:**\n\n"
        for i, r in enumerate(results['results'][:3], 1):
            output += f"**{i}. {r.get('title','Recipe')}**\n"
            output += f"{r.get('content','')[:150]}...\n"
            output += f"🔗 {r.get('url','')}\n\n"
        return output
    except Exception as e:
        print(f"[Web Search] Error: {e}")
        return None
    
    
# ==============================
# 🤖 AGENT: SELECT BEST TOOL
# ==============================
def agent_select_tool(user_input, state):
    """Dynamically select the best tool based on user state"""
    ingredients_info = ', '.join(state['ingredients']) if state['ingredients'] else 'none'
    ingredient_count = len(state['ingredients'])

    prompt = f"""You are an intelligent agent controller for a food assistant.

Current situation:
- User said: "{user_input}"
- Known ingredients: {ingredients_info} ({ingredient_count} total)
- User preference: {state['preference'] or 'not stated'}

Choose ONE tool:
- search_database: if user has 2+ ingredients (search local recipes)
- generate_recipe: if user has 1+ ingredients (create custom recipe)
- ask_clarification: ONLY if 0 ingredients AND user hasn't stated what they want
- greeting: if user is just saying hello/greeting

RULE: If user has 1+ ingredients, ALWAYS pick generate_recipe or search_database.
Only ask for clarification if they have NO ingredients.

Respond with ONLY the tool name. Nothing else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.1
        )
        
        tool = response.choices[0].message.content.strip().lower()
        valid_tools = ["search_database", "generate_recipe", "ask_clarification", "greeting"]
        
        if tool not in valid_tools:
            tool = "generate_recipe" if ingredient_count > 0 else "ask_clarification"

        # ✅ Hard override rules
        if ingredient_count == 0:
            tool = "ask_clarification"
        elif ingredient_count >= 1:
            # Always try to make recipe if we have ingredients
            if tool == "ask_clarification":
                tool = "generate_recipe"

        print(f"[Agent] 🛠️ Tool selected: {tool} (ingredients: {ingredient_count})")
        return tool
        
    except Exception as e:
        print(f"[Agent] ❌ Tool selection error: {e}")
        return "generate_recipe" if ingredient_count > 0 else "ask_clarification"

# ==============================
# 🔄 AGENT: REASONING LOOP
# ==============================
def agent_reasoning_loop(user_input, state, user_id, max_attempts=3):
    """Main agentic reasoning loop with tool selection and verification"""
    thoughts = []
    ingredients = state["ingredients"]
    preference = state["preference"]

    # ⭐ NEW: Check if user is asking for SUGGESTIONS (English + Hindi + Marathi)
    suggestion_keywords = [
        # ENGLISH
        "what should i add", "what other ingredient", "what can i add",
        "how to make it more", "ingredients to add", "to make it healthier",
        "suggestions", "recommendations", "what to add",
        "ingrdients to add",
        
        # HINDI / HINGLISH
        "ky add kre",              # "What should I add"
        "kya add kru",             # "What should I add" (variant)
        "kya dalu",                # "What should I add"
        "aur kya",                 # "What else"
        "or kya",                  # "What else" (Hinglish)
        "or ingredients",          # "Other ingredients"
        "aur ingredients",         # "And ingredients"
        "swadish kaise",           # "How to make tasty"
        "swaadisht kaise",         # "How to make delicious"
        "healthy kaise",           # "How to make healthy"
        "aur sehat",               # "More healthy"
        "suggestions de",          # "Give suggestions"
        "suggestions dijiye",      # "Please give suggestions"
        "kya mila sakta",          # "What can be added"
        "isme aur kya",            # "What else in this"
        
        # MARATHI / MARATHI TRANSLITERATION
        "kay ghalu",               # "What should I add"
        "kay karu",                # "What should I do"
        "aankhi kay",              # "What else"
        "aanhi kay",               # "What else" (variant)
        "aarogya kar kase",        # "How to make healthy"
        "aarogykar kase",          # "How to make healthy" (variant)
        "swadisht kase",           # "How to make tasty"
        "aankhi ghalu",            # "Add more"
        "aanhi ghalu",             # "Add more" (variant)
        "kase sudhar",             # "How to improve"
        "kase tayyar",             # "How to prepare"
        "kase banvu",              # "How to make"
        "aankhi poshan",           # "More nutrition"
        "poshan badha",            # "Increase nutrition"
        "swad badha",              # "Increase taste"
        "suggestions de",          # "Give suggestions"
        "ky mhatva aahe",          # "What's important"
        "kahi badhkari",           # "Something additional"
        "aankhi ghalta yail",      # "What else can be added"
        "sudhaaravyu shakto",      # "Can be improved"
    ]
    
    asking_for_suggestions = any(kw in user_input.lower() for kw in suggestion_keywords)

    if asking_for_suggestions and ingredients:
        thoughts.append("💡 User asking for ingredient suggestions")
        
        suggestions_text = f"""Great question! 🥬 To make your **{' & '.join(ingredients).title()}** dish MORE healthy, here are ingredients you could ADD:

🥬 **Spinach** - Rich in iron, vitamins, minerals
🧅 **Onion** - Flavor, quercetin, antioxidants
🧄 **Garlic** - Immune-boost, anti-inflammatory
🌶️ **Green Chilli** - Vitamin C, metabolism boost
🥕 **Carrot** - Beta-carotene, natural sweetness
🍄 **Mushroom** - B vitamins, immune support
🥒 **Bell Pepper** - Vitamin C, antioxidants
🍃 **Coriander** - Digestive benefits, flavor
🫘 **Beans** - Protein, fiber

**Next Step:** Tell me which one you have! 
Example: "I have {ingredients[0]}, {ingredients[1]}, and spinach" 
Then I'll create a healthier recipe for you! 👨‍🍳"""
        
        return thoughts, suggestions_text

    # Check if user wants to make a specific dish with their ingredients
    specific_dishes = [
        "biryani", "pulao", "curry", "masala", "tikka", "korma",
        "fry", "roast", "sabzi", "dal", "daal", "sambar", "rasam",
        "dosa", "idli", "paratha", "naan", "roti", "paneer butter masala",
        "chicken curry", "egg curry", "fish curry", "mutton curry"
    ]
    
    # Extract dish name if user mentions one
    mentioned_dish = None
    for dish in specific_dishes:
        if dish in user_input.lower():
            mentioned_dish = dish
            break
    
    # If user wants specific dish AND has ingredients
    if mentioned_dish and ingredients:
        thoughts.append(f"🎯 User wants to make {mentioned_dish} with available ingredients")
        specific_recipe = generate_specific_dish_with_ingredients(mentioned_dish, ingredients, preference)
        if specific_recipe:
            return thoughts, specific_recipe
        
    # Recall persistent memory
    memories = get_memory(user_id, user_input)
    if memories:
        thoughts.append(f"📚 Memory: {', '.join(memories[:2])}")

    # ✅ Handle 0 ingredients immediately
    if not ingredients:
        thoughts.append("❌ No ingredients detected")
        return thoughts, ask_clarification(state)

    thoughts.append(f"🥘 Ingredients: {', '.join(ingredients)}")
    if preference:
        thoughts.append(f"📌 Preference: {preference}")

    # Attempt loop with verification
    for attempt in range(1, max_attempts + 1):
        thoughts.append(f"🔄 Attempt {attempt}/{max_attempts}")

        # THINK: Select tool
        tool = agent_select_tool(user_input, state)
        thoughts.append(f"🛠️ Tool: {tool}")

        # ACT: Execute tool
        output = None
        
        if tool == "greeting":
            return thoughts, "Hello! 😊 I'm Annapurna, your food assistant 🍛\n\nTell me what ingredients you have and I'll suggest the perfect recipe!"

        elif tool == "ask_clarification":
            return thoughts, ask_clarification(state)

        elif tool == "search_database":
            db_result = search_database(ingredients)
            if db_result:
                thoughts.append(f"✅ Found: {db_result.get('recipe_name')}")
                output = generate_with_ai(ingredients, preference, db_result, memories)
            else:
                thoughts.append("⚠️ DB miss → generating custom recipe")
                output = generate_with_ai(ingredients, preference, None, memories)

        elif tool == "generate_recipe":
            output = generate_with_ai(ingredients, preference, None, memories)

        # OBSERVE: Verify result
        if verify_result(output, ingredients):
            thoughts.append("✅ Verified: Recipe is valid")
            save_memory(user_id, f"User made recipe with: {', '.join(ingredients)}")
            state["last_recipe"] = output
            output = adjust_recipe(output, preference)
            return thoughts, output
        else:
            thoughts.append("⚠️ Verification failed, retrying...")
            state["attempt"] = attempt

    # All attempts failed → smart fallback
    thoughts.append("⚠️ Max attempts reached → fallback recipe")
    
    fallback = f"""🍛 **Simple {' & '.join(ingredients).title()} Dish**

Quick and easy recipe with what you have!

🧂 **Ingredients:**
- {(chr(10) + '- ').join(ingredients)}
- Salt and oil

📝 **Steps:**
1. Heat oil in a pan
2. Add {ingredients[0]} and cook for 2 minutes
3. {'Add ' + ingredients[1] + ' and mix well' if len(ingredients) > 1 else 'Season with salt'}
4. Cook for 5-7 minutes until soft
5. Serve hot! 🍽️

⏱️ **Time:** ~10 minutes

💡 **Why it works:** These ingredients complement each other perfectly!
"""

    return thoughts, adjust_recipe(fallback, preference)

# ==============================
# 📅 MEAL PLANNER
# ==============================
def generate_meal_plan(ingredients, days=3, preference=None):
    """Generate multi-day meal plan"""
    prompt = f"""You are Annapurna, Indian meal planning expert.

Available ingredients: {', '.join(ingredients)}
Days to plan: {days}
Preference: {preference or 'balanced'}

Create a {days}-day meal plan.
Assume basic pantry items (salt, oil, spices, onion).

Format EXACTLY:

📅 DAY 1
🌅 Breakfast: <dish> (X mins)
☀️ Lunch: <dish> (X mins)
🌙 Dinner: <dish> (X mins)

📅 DAY 2
...

Keep it realistic and use available ingredients."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a meal planning expert. Create practical Indian meal plans."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.4
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Meal Plan] Error: {e}")
        return "Could not generate meal plan. Try again!"

def handle_meal_plan_request(message, state):
    """Detect and handle meal plan requests"""
    triggers = [
        "meal plan", "plan my meals", "week plan",
        "3 day plan", "weekly", "plan for week"
    ]
    if any(t in message.lower() for t in triggers):
        if state["ingredients"]:
            days = 3
            if "week" in message.lower():
                days = 7
            elif "5 day" in message.lower():
                days = 5
            return generate_meal_plan(
                state["ingredients"],
                days,
                state["preference"]
            )
    return None

# ==============================
# 🍽️ DIRECT RECIPE REQUEST
# ==============================
def handle_direct_recipe_request(message):
    """
    If user asks for a specific recipe by name,
    generate it directly without needing ingredients.
    """
    # Expanded triggers for recipe requests
    triggers = [
        # English
        "recipe for", "how to make", "how to cook", "how to prepare",
        "make me", "give me recipe", "recipe of", "i want recipe",
        "show me recipe", "tell me recipe", "can you make",
        "can you cook", "i'd like to make", "i want to make",
        "recipe please", "share recipe", "teach me how to make",
        
        # Hindi/Urdu
        "kaise banate", "kaise banaye", "kaise banta", "kaise banau",
        "recipe batao", "recipe chahiye", "banana hai", "banana chahta",
        "banana chahti", "batao kaise", "kese banaye",
        
        # Marathi
        "kasa banvaycha", "recipe sangaa", "kasa karaycha",
        "kas banvu", "kashi banvaychi", "recipe de",
        
        # Direct dish names (common patterns)
        r"\b(chicken\s+biryani|biryani)\b",
        r"\b(paneer\s+butter\s+masala|butter\s+paneer)\b",
        r"\b(daal\s+makhani|dal\s+makhani)\b",
        r"\b(chicken\s+tikka\s+masala)\b",
        r"\b(palak\s+paneer|palak\s+paneer)\b",
        r"\b(masala\s+dosa|dosa)\b",
        r"\b(pav\s+bhaji|pavbhaji)\b",
        r"\b(chole\s+bhature|chole)\b",
        r"\b(fish\s+curry|fish\s+masala)\b",
        r"\b(egg\s+curry|anda\s+curry)\b",
        r"\b(mutton\s+curry|mutton\s+masala)\b",
        r"\b(veg\s+biryani|vegetable\s+biryani)\b"
    ]
    
    message_lower = message.lower().strip()
    
    # Check if it's a recipe request
    is_recipe_request = False
    requested_dish = None
    
    for trigger in triggers:
        if trigger.startswith(r'\b'):  # It's a regex pattern for dish names
            import re
            match = re.search(trigger, message_lower, re.IGNORECASE)
            if match:
                is_recipe_request = True
                requested_dish = match.group(0)
                break
        elif trigger in message_lower:
            is_recipe_request = True
            # Extract dish name from the message
            dish = message_lower.replace(trigger, "").strip()
            for word in ["please", "pls", "for me", "right now", "quickly"]:
                dish = dish.replace(word, "").strip()
            if dish and len(dish) > 2:
                requested_dish = dish
            break
    
    if not is_recipe_request:
        return None
    
    # If no specific dish was extracted, ask for clarification
    if not requested_dish or len(requested_dish) < 3:
        return """🍛 **Which recipe would you like?**

Please tell me the dish name, for example:
- "Chicken Biryani"
- "Paneer Butter Masala"
- "Dal Makhani"
- "Masala Dosa"

Or just type the dish name directly! 👨‍🍳"""
    
    print(f"[DirectRecipe] 🍳 Generating recipe for: {requested_dish}")
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are Annapurna, an expert Indian cooking assistant.
When user asks for a recipe, give a COMPLETE, AUTHENTIC, DETAILED recipe.
Always format your response as:

🍛 **Dish Name** (with a star rating like ⭐⭐⭐⭐)

📖 **About this dish:**
2-3 sentences describing the dish, its origin, and what makes it special.

🧂 **Ingredients:**
- List all ingredients with exact quantities
- Group by categories (e.g., "For Marinade:", "For Gravy:", "For Tempering:")
- Include all essential spices

📝 **Step-by-Step Instructions:**
1. First step with details (time/temperature)
2. Second step with details
3. Continue with clear instructions

⏱️ **Cooking Time:** Prep: X mins | Cook: Y mins | Total: Z mins
👥 **Servings:** X people
🔥 **Difficulty:** Easy/Medium/Hard

💡 **Pro Tips:**
- Tip 1
- Tip 2

🍽️ **Serving Suggestions:**
What to serve with this dish"""
                },
                {
                    "role": "user",
                    "content": f"Give me a complete, authentic recipe for {requested_dish}. Include all details like a professional chef would."
                }
            ],
            max_tokens=1200,
            temperature=0.4
        )
        result = response.choices[0].message.content
        print(f"[DirectRecipe] ✅ Generated recipe for: {requested_dish}")
        return result

    except Exception as e:
        print(f"[DirectRecipe] Error: {e}")
        return f"""❌ **Sorry, I couldn't generate the recipe for {requested_dish} right now.**

Please try:
1. Typing the dish name clearly (e.g., "Chicken Biryani recipe")
2. Check your internet connection
3. Try again in a moment

Or tell me your ingredients and I'll suggest a recipe! 🍛"""
        
# ==============================
# 🎯 MAIN CHAT HANDLER
# ==============================
def respond(message, history):
    """Main entry point from Gradio UI"""
    if not message.strip():
        yield history
        return

    # ⭐ NEW: Check for bad words FIRST
    has_bad_words, detected_language = detect_bad_words(message)
    
    if has_bad_words:
        punch_line = get_punch_line(detected_language)
        history.append({"role": "user", "content": message})
        history.append({
            "role": "assistant", 
            "content": punch_line
        })
        print(f"[BadWords] Blocked message with bad words in {detected_language}")
        yield history
        return

    user_id = "default"
    history.append({"role": "user", "content": message})

    try:
        # ✅ PIPELINE: Normalize → Spell Fix → Intent → State → Reason
        normalized = normalize_user_input(message)
        fixed = fix_spelling(normalized)
        intent = detect_intent(fixed)
        state = update_state(user_id, fixed)

        print(f"\n[Pipeline] Intent: {intent} | Ingredients: {state['ingredients']} | Pref: {state['preference']}\n")

        # Handle closing intent
        if intent == "closing":
            history.append({
                "role": "assistant",
                "content": "Thank you! Happy cooking! 🍛\n\nCome back anytime you need a recipe. Bon appétit! 🤌"
            })
            yield history
            return

        # ✅ Main agentic reasoning loop
        # ✅ Main agentic reasoning loop
        thoughts, reply = agent_reasoning_loop(fixed, state, user_id)
        thinking_text = "\n".join([f"👉 {t}" for t in thoughts])

        # Build extra info
        extra_info = ""
        if state["ingredients"]:
                extra_info += calculate_nutrition(state["ingredients"])
                extra_info += get_cooking_metrics(state["ingredients"])
        if "shopping" in fixed.lower() or "list" in fixed.lower():
            extra_info += generate_shopping_list(reply)

        final_output = f"""🤖 **Thinking Process:**
    {thinking_text}

---

{reply}

{extra_info}"""

        history.append({"role": "assistant", "content": final_output})
        yield history

    except Exception as e:
        print(f"[Error] {e}")
        error_response = f"❌ Oops! Something went wrong: {str(e)}\n\nPlease try again with your ingredients."
        history.append({"role": "assistant", "content": error_response})
        yield history

# ==============================
# 🎨 UI CONSTANTS
# ==============================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── BASE ── */
body, .gradio-container {
    background: #0e0600 !important;
    font-family: 'DM Sans', sans-serif !important;
    min-height: 100vh;
}

/* ── ANIMATED GRADIENT BG ── */
.gradio-container::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 80% 60% at 10% 20%, rgba(180,60,0,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 80% at 90% 80%, rgba(120,40,0,0.15) 0%, transparent 60%),
        radial-gradient(ellipse 50% 50% at 50% 50%, rgba(245,180,30,0.06) 0%, transparent 70%);
}

/* ── FOOD FLOAT BG ── */
.food-float-bg { position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0; overflow:hidden; }
.food-emoji { position:absolute; opacity:0.10; animation:floatUp linear infinite; filter:drop-shadow(0 2px 8px rgba(245,180,30,0.15)); }
@keyframes floatUp {
    0%   { transform:translateY(110vh) rotate(0deg);   opacity:0; }
    10%  { opacity:0.10; }
    90%  { opacity:0.10; }
    100% { transform:translateY(-10vh) rotate(360deg); opacity:0; }
}

/* ── CHATBOT ── */
.chatbot {
    background: rgba(30,10,0,0.7) !important;
    border: 1px solid rgba(245,180,30,0.18) !important;
    border-radius: 20px !important;
    backdrop-filter: blur(12px) !important;
}

/* ── INPUTS ── */
textarea, input[type="text"] {
    background: rgba(40,15,0,0.8) !important;
    border: 1px solid rgba(245,180,30,0.25) !important;
    border-radius: 14px !important;
    color: #f5e6c8 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: border-color 0.3s !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: rgba(245,180,30,0.6) !important;
    box-shadow: 0 0 0 3px rgba(245,180,30,0.08) !important;
}

/* ── BUTTONS ── */
button.primary {
    background: linear-gradient(135deg, #f5c842 0%, #e8873a 50%, #c0392b 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #1a0a00 !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: 0.5px !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    box-shadow: 0 4px 20px rgba(245,180,30,0.25) !important;
}
button.primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(245,180,30,0.38) !important;
}
button.secondary {
    background: rgba(245,180,30,0.08) !important;
    border: 1px solid rgba(245,180,30,0.22) !important;
    color: #f5d98a !important;
    border-radius: 14px !important;
    transition: background 0.2s, border-color 0.2s !important;
}
button.secondary:hover {
    background: rgba(245,180,30,0.15) !important;
    border-color: rgba(245,180,30,0.4) !important;
}

/* ── TABS ── */
.tab-nav button {
    color: #c8a060 !important;
    border-bottom: 2px solid transparent !important;
    font-weight: 500 !important;
    transition: color 0.2s, border-color 0.2s !important;
}
.tab-nav button.selected {
    color: #f5c842 !important;
    border-bottom: 2px solid #f5c842 !important;
    background: transparent !important;
}

/* ── MARKDOWN ── */
.markdown p, .markdown li { color: #e8c890 !important; line-height: 1.8 !important; }
.markdown strong { color: #f5c842 !important; }
.markdown h1,.markdown h2,.markdown h3 { color: #f5c842 !important; font-family: 'Playfair Display', serif !important; }

/* ── SLIDER ── */
input[type=range] { accent-color: #f5c842 !important; }

/* ── RADIO ── */
.gr-radio label { color: #e8c890 !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: rgba(245,180,30,0.04); }
::-webkit-scrollbar-thumb { background: rgba(245,180,30,0.25); border-radius: 10px; }
/* ── PILL INPUT BAR ── */
.gradio-container .gap-2:has(textarea),
.gradio-container .gr-group:has(textarea) {
    background: #1e1e1e !important;
    border-radius: 999px !important;
    border: 0.5px solid #3a3a3a !important;
    padding: 4px 12px !important;
    align-items: center !important;
}
textarea {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    color: #cccccc !important;
    font-size: 15px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    padding: 6px 4px !important;
    resize: none !important;
}
textarea:focus {
    border: none !important;
    box-shadow: none !important;
}
button.primary {
   send-btn {
    background: #ffffff !important;
    color: #111 !important;
    border-radius: 50% !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    font-size: 18px !important;
}
}
"""

FLOAT_HTML = """
<div class='food-float-bg' id='floatBg'></div>
<script>
const foods=['🍅','🧅','🥔','🥬','🥕','🍗','🥚','🍚','🫘','🧄','🌶️','🍋','🧀','🍄','🌽','🍛','🍲','🥗','🫕','🍳','🥦','🧆','🥘','🫚','🥩','🍱','🧆','🫙'];
function spawnFood(){
    const bg=document.getElementById('floatBg');
    if(!bg)return;
    const el=document.createElement('div');
    el.className='food-emoji';
    el.textContent=foods[Math.floor(Math.random()*foods.length)];
    el.style.left=Math.random()*95+'%';
    el.style.fontSize=(16+Math.random()*20)+'px';
    const dur=12+Math.random()*14;
    el.style.animationDuration=dur+'s';
    el.style.animationDelay=(Math.random()*4)+'s';
    bg.appendChild(el);
    setTimeout(()=>el.remove(),(dur+5)*1000);
}
setInterval(spawnFood,800);
for(let i=0;i<18;i++)setTimeout(spawnFood,i*200);
</script>
"""


# ==============================
# 🎨 GRADIO UI
# ==============================
with gr.Blocks(css=custom_css) as app:
    gr.HTML(FLOAT_HTML)
    gr.HTML("""
    <style>
        /* Contact modal */
        #contactModal {
            display:none; position:fixed; inset:0; z-index:9999;
            background:rgba(0,0,0,0.72); backdrop-filter:blur(6px);
            align-items:center; justify-content:center;
        }
        #contactModal.open { display:flex; }
        .modal-card {
            background: linear-gradient(160deg, #1e0a00 0%, #2d1200 60%, #1a0800 100%);
            border: 1px solid rgba(245,180,30,0.28);
            border-radius: 24px;
            padding: 36px 40px;
            width: 420px; max-width:92vw;
            box-shadow: 0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(245,180,30,0.08);
            position:relative;
            animation: popIn 0.28s cubic-bezier(.34,1.56,.64,1);
        }
        @keyframes popIn {
            from { transform:scale(0.88); opacity:0; }
            to   { transform:scale(1);    opacity:1; }
        }
        .modal-close {
            position:absolute; top:14px; right:18px;
            background:rgba(245,180,30,0.1); border:none;
            color:#f5c842; font-size:20px; width:32px; height:32px;
            border-radius:50%; cursor:pointer; line-height:32px; text-align:center;
            transition:background 0.2s;
        }
        .modal-close:hover { background:rgba(245,180,30,0.22); }
        .contact-btn {
            display:flex; align-items:center; gap:12px;
            padding:13px 18px; border-radius:14px; margin:10px 0;
            text-decoration:none;
            border:1px solid rgba(245,180,30,0.15);
            background:rgba(245,180,30,0.06);
            transition:background 0.2s, border-color 0.2s, transform 0.15s;
        }
        .contact-btn:hover {
            background:rgba(245,180,30,0.13);
            border-color:rgba(245,180,30,0.35);
            transform:translateX(4px);
        }
        .contact-btn .icon-wrap {
            width:38px; height:38px; border-radius:10px;
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
        }
        .contact-divider {
            border:none; border-top:1px solid rgba(245,180,30,0.12);
            margin:18px 0 14px;
        }
    </style>

    <!-- ░░ CONTACT MODAL ░░ -->
    <div id='contactModal'>
        <div class='modal-card'>
            <button class='modal-close' onclick="document.getElementById('contactModal').classList.remove('open')">✕</button>

            <!-- Avatar + Name -->
            <div style='text-align:center; margin-bottom:22px;'>
                <div style='width:64px;height:64px;border-radius:50%;
                            background:linear-gradient(135deg,#f5c842,#e8873a);
                            display:flex;align-items:center;justify-content:center;
                            margin:0 auto 12px; font-size:28px;'>👨‍🍳</div>
                <h2 style='margin:0;color:#f5c842;font-family:Playfair Display,serif;font-size:22px;'>Sahil Suryawanshi</h2>
                <p style='margin:4px 0 0;color:#c8a060;font-size:12px;letter-spacing:2px;text-transform:uppercase;'>AI Developer &amp; Engineer</p>
            </div>

            <hr class='contact-divider'>

            <!-- LinkedIn -->
            <a class='contact-btn' href='https://www.linkedin.com/in/sahil585/' target='_blank'>
                <div class='icon-wrap' style='background:rgba(10,102,194,0.18);'>
                    <svg width='20' height='20' viewBox='0 0 24 24' fill='#5baee8'>
                        <path d='M20.45 20.45h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.354V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'/>
                    </svg>
                </div>
                <div>
                    <p style='margin:0;color:#f5e6c8;font-size:13px;font-weight:600;'>LinkedIn Profile</p>
                    <p style='margin:2px 0 0;color:#8ab4cc;font-size:11px;'>linkedin.com/in/sahil585</p>
                </div>
            </a>

            <!-- Email -->
            <a class='contact-btn' href='mailto:suryawanshisahil585@gmail.com'>
                <div class='icon-wrap' style='background:rgba(234,67,53,0.15);'>
                    <svg width='20' height='20' viewBox='0 0 24 24' fill='none'
                         stroke='#f08070' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                        <path d='M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'/>
                        <polyline points='22,6 12,13 2,6'/>
                    </svg>
                </div>
                <div>
                    <p style='margin:0;color:#f5e6c8;font-size:13px;font-weight:600;'>Email Me</p>
                    <p style='margin:2px 0 0;color:#c88a80;font-size:11px;'>suryawanshisahil585@gmail.com</p>
                </div>
            </a>

            <!-- GitHub placeholder (optional) -->
            <a class='contact-btn' href='https://github.com/Sahil05-08' target='_blank'>
                <div class='icon-wrap' style='background:rgba(255,255,255,0.07);'>
                    <svg width='20' height='20' viewBox='0 0 24 24' fill='#c8c8c8'>
                        <path d='M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12'/>
                    </svg>
                </div>
                <div>
                    <p style='margin:0;color:#f5e6c8;font-size:13px;font-weight:600;'>GitHub</p>
                    <p style='margin:2px 0 0;color:#a0a0b0;font-size:11px;'>github.com/sahil585</p>
                </div>
            </a>

            <hr class='contact-divider'>
            <p style='text-align:center;color:#8a6a40;font-size:11px;margin:0;'>
                🍛 Built with passion for food &amp; AI
            </p>
        </div>
    </div>

    <!-- ░░ HEADER ░░ -->
    <div style='position:relative; padding:28px 0 14px;'>

        <!-- Decorative spice dots -->
        <div style='position:absolute;top:10px;left:50%;transform:translateX(-50%);
                    width:80px;height:2px;
                    background:linear-gradient(90deg,transparent,rgba(245,180,30,0.4),transparent);
                    border-radius:2px;'></div>

<!-- ── CENTER: Title ── -->
<div style='text-align:center; padding: 40px 0 20px;'>
    <h1 style='font-family:Playfair Display,serif; color:#f5c842;
               font-size:72px; margin:0; line-height:1.1;
               text-shadow:0 2px 30px rgba(245,180,30,0.35),
                           0 0 60px rgba(245,130,30,0.15);
               letter-spacing:2px;'>
        🍛 Annapurna AI
    </h1>
    <p style='color:#c8903a; letter-spacing:4px; text-transform:uppercase;
              font-size:14px; margin:10px 0 0; font-weight:500;'>
        Agentic Cooking Assistant
    </p>
    <p style='color:rgba(245,200,66,0.5); font-size:14px;
              margin:8px 0 0; letter-spacing:1px;'>
        Made by <span style='color:#f5d98a; font-weight:600;'>Sahil Suryawanshi</span>
    </p>

    <!-- Spice tags -->
    <div style='display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap;'>
        <span style='background:rgba(245,180,30,0.1);border:1px solid rgba(245,180,30,0.2);
                     border-radius:20px;padding:4px 14px;color:#c8903a;
                     font-size:10px;letter-spacing:1px;'>🌶️ SPICY</span>
        <span style='background:rgba(245,180,30,0.1);border:1px solid rgba(245,180,30,0.2);
                     border-radius:20px;padding:4px 14px;color:#c8903a;
                     font-size:10px;letter-spacing:1px;'>🥗 HEALTHY</span>
        <span style='background:rgba(245,180,30,0.1);border:1px solid rgba(245,180,30,0.2);
                     border-radius:20px;padding:4px 14px;color:#c8903a;
                     font-size:10px;letter-spacing:1px;'>⚡ QUICK</span>
        <span style='background:rgba(245,180,30,0.1);border:1px solid rgba(245,180,30,0.2);
                     border-radius:20px;padding:4px 14px;color:#c8903a;
                     font-size:10px;letter-spacing:1px;'>🤖 AI POWERED</span>
    </div>
</div>

    <!-- Divider -->
    <div style='height:1px;background:linear-gradient(90deg,transparent,rgba(245,180,30,0.2),transparent);margin:0 20px 4px;'></div>
    """)

    with gr.Tabs():
        # ── TAB 1: CHAT ──
        with gr.Tab("💬 Chat"):
                chatbot = gr.Chatbot(
                value=[{"role": "assistant",
                "content": """🍛 **Welcome to Annapurna AI!** 👨‍🍳

                I'm your AI cooking assistant. Here's what you can do:

                ✅ **DIRECT RECIPE REQUESTS:** (NEW!)
                • "Give me Chicken Biryani recipe"
                • "How to make Paneer Butter Masala"
                • "Butter Chicken recipe please"
                • "Dal Makhani kaise banaye"

                ✅ **TELL ME INGREDIENTS:**
                • "I have paneer and tomato"
                • "potato, onion, spinach"

                ✅ **TELL ME PREFERENCES:**
                • "Make it spicy" 🌶️
                • "I want something healthy" 🥗
                • "Quick recipe under 15 mins" ⚡

                ✅ **USE VOICE:**
                • 🎙️ Click "Tap to speak" & tell ingredients

                ✅ **SCAN FRIDGE:**
                • 📸 Upload a fridge photo → AI detects ingredients

                ✅ **MEAL PLANNING:**
                • 📅 Generate 3-7 day meal plans

                **Try now:** 
                • Type "Chicken Biryani recipe" for direct recipe 🍗
                • Or "I have egg and bread" for custom recipe 👇"""}],
            )
                
                with gr.Row():
                   gr.Markdown("### 💡 Quick Examples:")
    
                with gr.Row():
                    ex1 = gr.Button("🥚 Egg + Bread", size="sm")
                    ex2 = gr.Button("🥔 Potato + Onion", size="sm")
                    ex3 = gr.Button("🌶️ Spicy Recipe", size="sm")
                    ex4 = gr.Button("⚡ Quick 10min", size="sm")
 

                with gr.Row():
                    msg = gr.Textbox(
                    placeholder="Ask anything...",
                    scale=6,
                    show_label=False,
                    lines=1,
                    max_lines=1,
                    container=False,
                    )
                    send = gr.Button("➤", variant="primary", scale=1, min_width=36)
                    gr.HTML("""
                    <div style='background:rgba(245,200,66,0.05); border-radius:12px; padding:12px; margin-top:12px;'>
    <p style='color:#e8a06a; font-size:12px; margin:0; line-height:1.6;'>
        💡 <strong>Quick Start:</strong> 
        • Ask for any recipe: <strong>"Chicken Biryani recipe"</strong> 🍗
        • Or type ingredients: <strong>"paneer, tomato"</strong> 🥘
        • Use voice 🎙️ | See <strong>❓ How to Use</strong> tab for help
    </p>
</div>
""")
    # ── Voice input row ──
                with gr.Row():
                    audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎙️ Tap to speak",
                    scale=4
                    )
                    voice_btn = gr.Button("🎙️ Send Voice", variant="secondary", scale=1)

                clear = gr.Button("🗑️ New Chat", variant="secondary")

    # ── Voice handler ──
                def handle_voice(audio_path, history):
                    text = transcribe_audio(audio_path)
                    if not text:
                        history.append({"role": "assistant",
                            "content": "⚠️ Couldn't hear that. Try again!"})
                        yield history, ""
                        return
                    for updated_history in full_respond(text, history):
                        yield updated_history, ""

                voice_btn.click(handle_voice, [audio_input, chatbot], [chatbot, msg])

        # ── TAB 2: FRIDGE SCAN ──
        with gr.Tab("📸 Fridge Scan"):
            gr.HTML("""
    <div style='background:rgba(245,180,30,0.08); border-radius:14px; 
                padding:20px; text-align:center; margin-bottom:20px;'>
    <h3 style='color:#f5c842; margin:0;'>📸 Smart Ingredient Detection</h3>
    <p style='color:#e8a06a; margin:8px 0 0;'>
    Upload a clear photo of your fridge or kitchen. AI will automatically detect all visible ingredients!
    </p>
    <p style='color:#c8a060; font-size:12px; margin:8px 0;'>
        ✅ Best results with clear, well-lit photos
    </p>
    </div>
    """)
    
    # ✅ ADD THESE COMPONENTS:
            image_input = gr.Image(type="filepath", label="📸 Upload Fridge Photo", scale=2)
            scan_btn = gr.Button("🔍 Detect Ingredients", variant="primary")
            scan_output = gr.Textbox(label="📋 Detected Ingredients", interactive=True)
            use_btn = gr.Button("✅ Use These Ingredients", variant="secondary")

        # ── TAB 3: MEAL PLANNER ──
                # ── TAB 3: MEAL PLANNER ──
        with gr.Tab("📅 Meal Planner"):
            gr.HTML("""
            <div style='background:rgba(245,180,30,0.08); border-radius:14px; 
                        padding:20px; text-align:center; margin-bottom:20px;'>
                <h3 style='color:#f5c842; margin:0;'>📅 Multi-Day Meal Planning</h3>
                <p style='color:#e8a06a; margin:8px 0;'>
                    Plan breakfast, lunch & dinner for 3-7 days using your ingredients!
                </p>
                <p style='color:#c8a060; font-size:12px; margin:8px 0;'>
                    Example: Type "paneer, tomato, spinach, potato" → Get 3-day meal plan
                </p>
            </div>
            """)
            
            gr.HTML("""
            <div style='background:rgba(245,200,66,0.05); border-left:3px solid rgba(245,200,66,0.3);
                        padding:12px; border-radius:8px; margin-bottom:16px;'>
                <p style='color:#f5d98a; margin:0; font-size:13px;'>
                    💡 <strong>Tip:</strong> Use comma-separated ingredients (e.g., "egg, bread, milk")
                </p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    plan_ingredients = gr.Textbox(
                        label="🥘 Ingredients",
                        placeholder="e.g., paneer, tomato, onion, spinach",
                        lines=2
                    )
                    plan_days = gr.Slider(3, 7, value=3, step=1, label="📅 Days")
                    plan_pref = gr.Dropdown(
                        ["balanced", "spicy", "healthy", "quick", "vegan"],
                        value="balanced",
                        label="📌 Preference"
                    )
                    plan_btn = gr.Button("📋 Generate Meal Plan", variant="primary")
                
                with gr.Column(scale=5):
                    plan_output = gr.Textbox(
                        label="📅 Your Meal Plan",
                        lines=35,
                        max_lines=60,
                        interactive=False,
                        elem_id="meal-plan-output"
                    )
            
            gr.HTML("""
            <style>
                #meal-plan-output textarea {
                    min-height: 550px !important; 
                    font-size: 14px !important;
                    line-height: 1.6 !important;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                    background-color: rgba(0,0,0,0.2) !important;
                    border: 1px solid rgba(245,200,66,0.2) !important;
                    padding: 15px !important;
                }
                #meal-plan-output {
                    height: auto !important;
                }
            </style>
            """)

        # ── TAB 4: ABOUT ──
        with gr.Tab("👤 About"):
            gr.HTML("""
    <div style='max-width:560px; margin:40px auto; text-align:center;'>

        <!-- Avatar -->
        <div style='width:80px;height:80px;border-radius:50%;
                    background:linear-gradient(135deg,#f5c842,#e8873a);
                    display:flex;align-items:center;justify-content:center;
                    margin:0 auto 18px; font-size:36px;
                    box-shadow:0 8px 32px rgba(245,180,30,0.25);'>👨‍🍳</div>

        <h2 style='color:#f5c842;font-family:Playfair Display,serif;
                   font-size:26px;margin:0;'>Sahil Suryawanshi</h2>
        <p style='color:#c8a060;font-size:11px;letter-spacing:3px;
                  text-transform:uppercase;margin:6px 0 20px;'>AI Developer & Engineer</p>

        <p style='color:#e8c890;font-size:14px;line-height:1.8;
                  margin:0 0 28px;padding:0 20px;'>
            Built <strong style='color:#f5c842;'>Annapurna AI</strong> — an agentic cooking
            assistant that detects ingredients, suggests recipes, plans meals,
            and speaks recipes aloud. Powered by Groq, ChromaDB & edge-tts.
        </p>

        <!-- Icon links -->
        <div style='display:flex;gap:16px;justify-content:center;margin-top:10px;'>

            <a href='https://www.linkedin.com/in/sahil585/' target='_blank' title='LinkedIn'
               style='width:52px;height:52px;border-radius:16px;
                      background:rgba(10,102,194,0.18);border:1px solid rgba(10,102,194,0.35);
                      display:flex;align-items:center;justify-content:center;text-decoration:none;
                      transition:transform 0.2s;'
               onmouseover="this.style.transform='translateY(-4px)'"
               onmouseout="this.style.transform='translateY(0)'">
                <svg width='24' height='24' viewBox='0 0 24 24' fill='#5baee8'>
                    <path d='M20.45 20.45h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.354V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z'/>
                </svg>
            </a>

            <a href='mailto:suryawanshisahil585@gmail.com' title='Email'
               style='width:52px;height:52px;border-radius:16px;
                      background:rgba(234,67,53,0.15);border:1px solid rgba(234,67,53,0.35);
                      display:flex;align-items:center;justify-content:center;text-decoration:none;
                      transition:transform 0.2s;'
               onmouseover="this.style.transform='translateY(-4px)'"
               onmouseout="this.style.transform='translateY(0)'">
                <svg width='24' height='24' viewBox='0 0 24 24' fill='none'
                     stroke='#f08070' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>
                    <path d='M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z'/>
                    <polyline points='22,6 12,13 2,6'/>
                </svg>
            </a>

            <a href='https://github.com/Sahil05-08' target='_blank' title='GitHub'
               style='width:52px;height:52px;border-radius:16px;
                      background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.18);
                      display:flex;align-items:center;justify-content:center;text-decoration:none;
                      transition:transform 0.2s;'
               onmouseover="this.style.transform='translateY(-4px)'"
               onmouseout="this.style.transform='translateY(0)'">
                <svg width='24' height='24' viewBox='0 0 24 24' fill='#c8c8c8'>
                    <path d='M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12'/>
                </svg>
            </a>

        </div>

        <p style='color:rgba(245,180,30,0.3);font-size:11px;margin-top:32px;'>
            🍛 Built with passion for food & AI
        </p>
    </div>
    """)

        with gr.Tab("❓ How to Use"):
            gr.Markdown("""
# 🎯 How to Use Annapurna AI

## **Method 1: Direct Recipe Request** 🍛 (NEW!)
Simply ask for any recipe by name - NO ingredients needed!

**Examples:**
- "Give me Chicken Biryani recipe"
- "How to make Paneer Butter Masala"
- "Butter Chicken recipe please"
- "Dal Makhani kaise banaye"
- "Masala Dosa recipe"
- "Egg Curry bana do"

**Works in multiple languages:**
- English: "Chicken Tikka Masala recipe"
- Hindi: "Paneer Butter Masala kaise banaye"
- Marathi: "Chicken Biryani recipe sangaa"

---

## **Method 2: Type Ingredients** 💬
Tell me what ingredients you have:

**Examples:**
- "I have paneer, tomato, spinach"
- "egg and bread only"
- "potato, onion, carrot"

**Add preferences:**
- "Make it spicy" 🌶️
- "I want something healthy" 🥗
- "Quick recipe under 15 mins" ⚡

---

## **Method 3: Voice Input** 🎙️
1. Click "Tap to speak"
2. Say your ingredients or recipe name clearly
3. Click "Send Voice"

**Examples:**
- *"Chicken Biryani recipe"*
- *"I have chicken and rice, make it healthy"*

---

## **Method 4: Fridge Photo** 📸
1. Go to **📸 Fridge Scan** tab
2. Upload a clear fridge photo
3. AI detects all ingredients automatically
4. Click "Use These Ingredients"

---

## **Method 5: Meal Planning** 📅
1. Go to **📅 Meal Planner** tab
2. Type your ingredients
3. Choose number of days (3-7)
4. Pick preference (healthy/spicy/etc)
5. Get full meal plan for all meals!

---

## **What You Can Ask** 💬

### **Direct Recipes (Any Indian dish):**
- Biryani, Pulao, Curry, Masala
- Tikka, Korma, Fry, Roast
- Dal, Sambar, Rasam
- Dosa, Idli, Paratha, Naan
- Paneer Butter Masala, Butter Chicken
- Egg Curry, Fish Curry, Mutton Curry
- And hundreds more!

### **With Your Ingredients:**
- "I have [ingredients] - suggest a recipe"
- "Make [dish name] with what I have"
- "Quick dinner using [ingredients]"

### **Recipe Modifications:**
- "Make it spicier" 🌶️
- "Make it healthier" 🥗
- "Add more protein" 💪
- "Make it vegan" 🌱
- "Make it faster" ⚡

### **Extra Features:**
- "Give me shopping list" 🛒
- "Show nutrition info" 📊
- "Plan my meals for 5 days" 📅
- "Suggestions to make it better" 💡

---

## **Example Conversations**

> **You:** "Chicken Biryani recipe"
> **AI:** *Gives complete recipe with ingredients, steps, cooking time, pro tips, and audio*

> **You:** "I have paneer, tomato, onion"
> **AI:** *Suggests Paneer Butter Masala recipe*

> **You:** "Make it spicy please"
> **AI:** *Adjusts recipe with more chili and spices*

> **You:** "Paneer Butter Masala kaise banaye"
> **AI:** *Gives recipe in Hinglish with detailed steps*

---

## **Pro Tips** 💡
- ✅ Be specific - "Chicken Biryani" works better than just "Biryani"
- ✅ Mention preferences for customized recipes
- ✅ Use voice for hands-free cooking
- ✅ Upload fridge photos to save typing
- ✅ Ask for meal plans to save time

---

**Happy Cooking!** 🍛👨‍🍳

*Annapurna AI - Your Intelligent Cooking Assistant*
""")

    # ==============================
    # 🔄 FULL RESPOND HANDLER
    # ==============================
    def full_respond(message, history):
        if not message.strip():
            yield history
            return

        has_bad, lang = detect_bad_words(message)
        if has_bad:
            history.append({"role":"user","content":message})
            history.append({"role":"assistant","content":get_punch_line(lang)})
            yield history
            return

        user_id = "default"
        history.append({"role":"user","content":message})

        try:
            normalized = normalize_user_input(message)
            fixed = fix_spelling(normalized)
            intent = detect_intent(fixed)
            state = update_state(user_id, fixed)

            if intent == "closing":
                history.append({"role":"assistant","content":"Happy cooking! 🍛 Come back anytime!"})
                yield history
                return

            # Check meal plan request
            meal_reply = handle_meal_plan_request(fixed, state)
            if meal_reply:
                history.append({"role":"assistant","content":meal_reply})
                yield history
                return
            # Check direct recipe request
                        # Check direct recipe request (using original message, not normalized)
            direct_recipe = handle_direct_recipe_request(message)  # Use original message
            if direct_recipe:
                audio_html = text_to_speech(direct_recipe)
                step_html = generate_step_mode(direct_recipe)
                nutrition = calculate_nutrition_for_recipe(direct_recipe)
                final = f"{direct_recipe}\n\n{step_html}\n\n{nutrition}\n   \n{audio_html}"
                history.append({"role":"assistant","content":final})
                yield history
                return

            # Check web search request
            web_triggers = [
            "web", "search", "online", "internet",
            "find recipe", "look up", "google",
            "search for recipe", "find online"
            ]
            if any(w in fixed.lower() for w in web_triggers):
                if state["ingredients"]:
                    web_result = search_web_recipes(state["ingredients"], state["preference"])
                    if web_result:
                        history.append({"role":"assistant","content":web_result})
                        yield history
                        return

            # Main agent loop
            thoughts, reply = agent_reasoning_loop(fixed, state, user_id)
            thinking_text = "\n".join([f"👉 {t}" for t in thoughts])

            # Build extras
            extra = ""
            if state["ingredients"]:
                extra += calculate_nutrition(state["ingredients"])
                extra += get_cooking_metrics(state["ingredients"])
            if "shopping" in fixed.lower() or "list" in fixed.lower():
                extra += generate_shopping_list(reply)

            # Step mode + Audio
            step_html = generate_step_mode(reply)
            audio_html = text_to_speech(reply)

            final = f"""🤖 **Agent Thinking:**
            {thinking_text}

            ---

            {reply}

            {extra}

            {step_html}

            {audio_html}"""

            history.append({"role":"assistant","content":final})
            yield history

        except Exception as e:
            print(f"[Error] {e}")
            history.append({"role":"assistant","content":f"❌ Error: {str(e)}\n\nPlease try again!"})
            return """❌ **I need ingredients!**

            Please tell me what you have. Examples:
            - "I have egg and bread"
            - "paneer, tomato, onion"
            - "potato and spinach"

            Or use the **📸 Fridge Scan** to upload a photo!"""
            yield history

            
   # ── EVENT HANDLERS ──
    send.click(full_respond, [msg, chatbot], chatbot).then(lambda: "", None, msg)
    msg.submit(full_respond, [msg, chatbot], chatbot).then(lambda: "", None, msg)
    clear.click(lambda: ([{"role":"assistant","content":"New chat! What ingredients do you have? 😊"}], ""),
    None, [chatbot, msg])

    # ✅ ADD THESE EXAMPLE BUTTON HANDLERS:
    def example_1():
        return "I have egg and bread"

    def example_2():
        return "I only have potato and onion"

    def example_3():
        return "paneer and tomato, make it spicy!"

    def example_4():
        return "egg, toast, make something quick under 10 minutes"

    ex1.click(example_1, None, msg)
    ex2.click(example_2, None, msg)
    ex3.click(example_3, None, msg)
    ex4.click(example_4, None, msg)

    # Photo scan handlers
    def run_scan(img):
        if img is None:
            return "⚠️ Please upload an image first!"
        result = detect_ingredients_from_image(img)
        if result:
            return result
        return "⚠️ Could not detect ingredients. Check terminal for errors, or try a clearer photo!"

    scan_btn.click(run_scan, image_input, scan_output)
    use_btn.click(full_respond, [scan_output, chatbot], chatbot)

    # Meal plan handler
    plan_btn.click(
        lambda ing, days, pref: generate_meal_plan(
            [i.strip() for i in ing.split(',') if i.strip()], int(days), pref
        ),
        [plan_ingredients, plan_days, plan_pref],
        plan_output
    )

    # ✅ VOICE HANDLER:
    def handle_voice(audio_path, history):
        text = transcribe_audio(audio_path)
        if not text:
            history.append({"role": "assistant","content": "⚠️ Couldn't hear that. Try again!"})
            yield history, ""
            return
        for updated_history in full_respond(text, history):
            yield updated_history, ""
    voice_btn.click(handle_voice, [audio_input, chatbot], [chatbot, msg])
    
    
# ==============================
# 🚀 RUN
# ==============================
if __name__ == "__main__":
    print("🍛 Starting Annapurna Food Assistant...")
    app.launch(share=False)




