"""
YouTube Long-Form Video Automation - Bilingual English/Korean Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5  # Target 5-minute videos (60 phrases)
TARGET_PHRASES = 60  # Number of phrases to generate

# English category names (for American/European learners)
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Korean translations for display
CATEGORIES_KOREAN = {
    "Motivation": "동기",
    "Love": "사랑",
    "Success": "성공",
    "Wisdom": "지혜",
    "Happiness": "행복",
    "Self Improvement": "자기계발",
    "Gratitude": "감사",
    "Friendship": "우정",
    "Hope": "희망",
    "Creativity": "창의성",
    "Inner Peace": "내면의 평화",
    "Confidence": "자신감",
    "Perseverance": "인내",
    "Inspiration": "영감",
    "Positive Life": "긍정적인 삶",
    "Courage": "용기",
    "Kindness": "친절",
    "Patience": "인내심",
    "Forgiveness": "용서",
    "Strength": "힘",
    "Joy": "기쁨",
    "Balance": "균형",
    "Growth": "성장",
    "Purpose": "목적",
    "Mindfulness": "마음챙김",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "ko-KR-SunHiNeural"

# Phrase history file (NEVER delete this!)
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    """Load all previously generated phrases"""
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    """Save phrase history"""
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    """Check if phrase was already generated (exact match)"""
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    """Check if a phrase is too similar to previously used phrases"""
    new_words = set(new_phrase.lower().split())

    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False

    for used in used_phrases:
        used_words = set(used.lower().split())

        if len(new_words) == 0 or len(used_words) == 0:
            continue

        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0

        if similarity >= similarity_threshold:
            return True

    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    """Filter out phrases that are too similar to previously used ones"""
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []

    for phrase in phrases:
        english_text = phrase.get("english", "")

        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] ⚠️ Skipping similar: {english_text[:50]}...")

    return unique_phrases


def add_phrases_to_history(phrases, category):
    """Add new phrases to history"""
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "korean": phrase["korean"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    """
    Calculate how many phrases needed for target video duration.
    Average phrase takes ~5 seconds (English ~2s + pause 0.5s + Korean ~2.5s)
    For 10 minutes (600 seconds): 600 / 5 = ~120 phrases
    """
    avg_phrase_duration = 5.0  # seconds
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    """Generate unique bilingual phrases for long-form video"""

    category_korean = CATEGORIES_KOREAN[category_english]

    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]

    viral_style = random.choice(VIRAL_STYLES)

    # Generate in batches to avoid API limits and ensure quality
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)

        if current_batch_size <= 0:
            break

        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }

                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Korean.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (with commas for natural pauses)
2. Korean translation (Hangul)
3. Korean pronunciation guide (romanization, e.g., "annyeonghaseyo")

Return as JSON array:
[{{"english": "...", "korean": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Korean teacher creating engaging educational content for YouTube. Create short, natural phrases with pauses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)

                # Filter by similarity
                filtered_phrases = filter_similar_phrases(phrases, history)

                # Filter by length and exact duplicates
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)

                # Add valid phrases
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)

                if len(all_phrases) >= num_phrases:
                    break

            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")

        # Small delay between batches
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    # Trim to exact count and save to history
    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)

    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    """Get fallback phrases, filtering out used ones with similarity check"""

    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "korean": "자신을 믿으세요.", "pronunciation": "jasin-eul mid-euseyo."},
            {"english": "You are capable of amazing things.", "korean": "당신은 놀라운 일을 할 수 있어요.", "pronunciation": "dangsin-eun nollaun il-eul hal su isseoyo."},
            {"english": "Dream big, start small.", "korean": "큰 꿈을 꾸고, 작게 시작하세요.", "pronunciation": "keun kkum-eul kkugo, jakge sijak-haseyo."},
            {"english": "Your future is created by your actions.", "korean": "당신의 미래는 당신의 행동으로 만들어져요.", "pronunciation": "dangsin-ui mirae-neun dangsin-ui haengdong-euro mandeureojyeoyo."},
            {"english": "Never give up on your dreams.", "korean": "꿈을 절대 포기하지 마세요.", "pronunciation": "kkum-eul jeoldae pogihaji maseyo."},
            {"english": "Small steps lead to big changes.", "korean": "작은 걸음이 큰 변화를 이끌어요.", "pronunciation": "jageun georeum-i keun byeonhwa-reul ikkeureoyo."},
            {"english": "You are stronger than you think.", "korean": "당신은 생각보다 더 강해요.", "pronunciation": "dangsin-eun saenggakboda deo ganghaeyo."},
        ],
        "Love": [
            {"english": "Love yourself first.", "korean": "먼저 자신을 사랑하세요.", "pronunciation": "meonjeo jasineul sarang-haseyo."},
            {"english": "Love makes everything possible.", "korean": "사랑은 모든 것을 가능하게 해요.", "pronunciation": "sarang-eun modeun geoseul ganeunghage haeyo."},
            {"english": "My heart beats for you.", "korean": "내 마음이 당신을 위해 뛰어요.", "pronunciation": "nae ma-eum-i dangsin-eul wihae ttwieoyo."},
            {"english": "You are my everything.", "korean": "당신은 나의 전부예요.", "pronunciation": "dangsin-eun naui jeonbu-yeyo."},
            {"english": "Together forever, hand in hand.", "korean": "영원히 함께, 손을 잡고.", "pronunciation": "yeong-wonhi hamkke, soneul japgo."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "korean": "성공은 노력에서 옵니다.", "pronunciation": "seonggong-eun noryeok-eseo omnida."},
            {"english": "Keep going, you're getting there.", "korean": "계속 나아가세요, 거의 다 왔어요.", "pronunciation": "gyesok naagaseyo, geoui da wasseoyo."},
            {"english": "Winners never quit.", "korean": "승자는 절대 포기하지 않아요.", "pronunciation": "seungja-neun jeoldae pogihaji anayo."},
            {"english": "Your effort will pay off.", "korean": "당신의 노력은 보답받을 거예요.", "pronunciation": "dangsin-ui noryeog-eun bodapbadeul geoyeyo."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "korean": "지식은 힘이에요.", "pronunciation": "jisik-eun him-ieyo."},
            {"english": "Learn from yesterday, live for today.", "korean": "어제에서 배우고 오늘을 살아가세요.", "pronunciation": "eoje-eseo baeugo oneureul saragaseyo."},
            {"english": "Think before you act.", "korean": "생각하고 행동하세요.", "pronunciation": "saenggakago haengdong-haseyo."},
            {"english": "Experience is the best teacher.", "korean": "경험은 최고의 스승이에요.", "pronunciation": "gyeongheom-eun choegoui seuseung-ieyo."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "korean": "행복은 선택이에요.", "pronunciation": "haengbog-eun seontaeg-ieyo."},
            {"english": "Find joy in the little things.", "korean": "작은 일에서 행복을 찾으세요.", "pronunciation": "jageun il-eseo haengbog-eul chajeuseyo."},
            {"english": "Smile, it makes others happy.", "korean": "미소 지으세요, 다른 사람도 기뻐해요.", "pronunciation": "miso jieuseyo, dareun saramdo gippeohaeyo."},
            {"english": "Today is a gift.", "korean": "오늘은 선물이에요.", "pronunciation": "oneul-eun seonmul-ieyo."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "korean": "어제보다 더 나아지세요.", "pronunciation": "eojeboda deo najiseyo."},
            {"english": "Grow through what you go through.", "korean": "겪는 일을 통해 성장하세요.", "pronunciation": "gyeokneun ireul tonghae seongjang-haseyo."},
            {"english": "Invest in yourself daily.", "korean": "매일 자신에게 투자하세요.", "pronunciation": "maeil jasinege tuja-haseyo."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "korean": "모든 것에 감사합니다.", "pronunciation": "modeun geose gamsahamnida."},
            {"english": "I appreciate your help.", "korean": "당신의 도움에 감사해요.", "pronunciation": "dangsin-ui doum-e gamsahaeyo."},
            {"english": "Grateful for this moment.", "korean": "이 순간에 감사해요.", "pronunciation": "i sungan-e gamsahaeyo."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "korean": "무슨 일이 있어도 영원한 친구예요.", "pronunciation": "museun iri isseodo yeong-wonhan chingu-yeyo."},
            {"english": "You are my best friend.", "korean": "당신은 내 가장 친한 친구예요.", "pronunciation": "dangsin-eun nae gajang chinhan chingu-yeyo."},
            {"english": "True friends stick together.", "korean": "진정한 친구는 함께해요.", "pronunciation": "jinjeonghan chinguneun hamkkehaeyo."},
        ],
        "Hope": [
            {"english": "There is always hope.", "korean": "항상 희망이 있어요.", "pronunciation": "hangsang huimang-i isseoyo."},
            {"english": "Better days are coming.", "korean": "더 좋은 날이 올 거예요.", "pronunciation": "deo joeun nar-i ol geoyeyo."},
            {"english": "Keep faith, keep going.", "korean": "믿음을 가지고 계속 나아가세요.", "pronunciation": "mideum-eul gajigo gyesok naagaseyo."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "korean": "오늘 아름다운 것을 만들어 보세요.", "pronunciation": "oneul areumdaun geoseul mandeureo boseyo."},
            {"english": "Your imagination is unlimited.", "korean": "당신의 상상력은 무한해요.", "pronunciation": "dangsin-ui sangsangnyeog-eun muhanhaeyo."},
            {"english": "Art comes from the heart.", "korean": "예술은 마음에서 나와요.", "pronunciation": "yesul-eun maeum-eseo nawayo."},
            {"english": "Express yourself freely.", "korean": "자유롭게 자신을 표현하세요.", "pronunciation": "jayuropge jasineul pyohyeon-haseyo."},
            {"english": "Innovation starts with curiosity.", "korean": "혁신은 호기심에서 시작됩니다.", "pronunciation": "hyeoksin-eun hogisim-eseo sijakdoemnida."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "korean": "당신 안에서 평화를 찾으세요.", "pronunciation": "dangsin an-eseo pyeonghwa-reul chajeuseyo."},
            {"english": "Breathe, relax, let go.", "korean": "숨 쉬고, 편안해지고, 놓아주세요.", "pronunciation": "sum swigo, pyeonanhaejigo, noajuseyo."},
            {"english": "Calm mind, happy heart.", "korean": "고요한 마음, 행복한 가슴.", "pronunciation": "goyohan maeum, haengbokan gaseum."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "korean": "당신은 충분해요, 지금 모습 그대로.", "pronunciation": "dangsin-eun chungbunhaeyo, jigeum moseup geudaero."},
            {"english": "Stand tall, speak up.", "korean": "당당하게 서서, 크게 말하세요.", "pronunciation": "dangdanghage seoseo, keuge mal-haseyo."},
            {"english": "Believe in your abilities.", "korean": "당신의 능력을 믿으세요.", "pronunciation": "dangsin-ui neungnyeogeul mideuseyo."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "korean": "절대 포기하지 말고 계속 나아가세요.", "pronunciation": "jeoldae pogihaji malgo gyesok naagaseyo."},
            {"english": "Storms make trees take deeper roots.", "korean": "폭풍이 나무 뿌리를 더 깊게 내리게 해요.", "pronunciation": "pokpung-i namu ppurireul deo gipge naerige haeyo."},
            {"english": "Patience and persistence win.", "korean": "인내와 끈기가 이깁니다.", "pronunciation": "gwaenchanhayo, modeun geosi da joajil geoyeyo."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "korean": "당신의 빛을 환하게 비추세요.", "pronunciation": "dangsin-ui bicheul hwanhage bichuseyo."},
            {"english": "Inspire others by your actions.", "korean": "행동으로 다른 사람에게 영감을 주세요.", "pronunciation": "haengdong-euro dareun saram-ege yeonggam-eul juseyo."},
            {"english": "Be the change you want to see.", "korean": "당신이 보고 싶은 변화가 되세요.", "pronunciation": "dangsin-i bogo sipeun byeonhwaga doeseyo."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "korean": "매일 긍정적인 마음을 선택하세요.", "pronunciation": "maeil geungjeongjeoin maeumeul seontaeghaseyo."},
            {"english": "Good vibes only.", "korean": "좋은 에너지만 가득.", "pronunciation": "joeun eneoji-man gadeuk."},
            {"english": "Life is what you make it.", "korean": "인생은 당신이 만드는 거예요.", "pronunciation": "insaeng-eun dangsin-i mandeuneun geoyeyo."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "korean": "용기를 내어 첫걸음을 내딛으세요.", "pronunciation": "yonggireul naeeo cheotgeoreumeul naedideuseyo."},
            {"english": "Courage is not the absence of fear.", "korean": "용기는 두려움이 없는 것이 아니에요.", "pronunciation": "yonggineun duryeoumi eomneun geosi anieyo."},
            {"english": "Face your fears head on.", "korean": "두려움을 정면으로 마주하세요.", "pronunciation": "duryeoum-eul jeongmyeon-euro maju-haseyo."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "korean": "만나는 모든 사람에게 친절하세요.", "pronunciation": "mannaneun modeun saram-ege chinjeol-haseyo."},
            {"english": "Kindness costs nothing, means everything.", "korean": "친절은 대가가 없지만 모든 것을 의미해요.", "pronunciation": "chinjeor-eun daegaga eopjiman modeun geoseul uimihaeyo."},
            {"english": "Spread kindness wherever you go.", "korean": "어디를 가든 친절을 나누세요.", "pronunciation": "eodireul gadeun chinjeoreul nanuseyo."},
        ],
        "Patience": [
            {"english": "Good things take time.", "korean": "좋은 일에는 시간이 필요해요.", "pronunciation": "joeun ire-neun sigani piryohaeyo."},
            {"english": "Wait patiently, trust the process.", "korean": "인내심을 가지고 과정을 믿으세요.", "pronunciation": "innaesimeul gajigo gwajeongeul mideuseyo."},
            {"english": "Rome wasn't built in a day.", "korean": "로마는 하루아침에 이루어지지 않았어요.", "pronunciation": "romaneun haruachime irueojiji anasseoyo."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "korean": "용서하고 자신을 자유롭게 하세요.", "pronunciation": "yongseohago jasineul jayuropge haseyo."},
            {"english": "Let go of grudges, find peace.", "korean": "원한을 놓고 평화를 찾으세요.", "pronunciation": "wonhan-eul nohgo pyeonghwaleul chajeuseyo."},
            {"english": "Forgiveness is a gift to yourself.", "korean": "용서는 자신에게 주는 선물이에요.", "pronunciation": "yongseoneun jasinege juneun seonmulieyo."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "korean": "당신은 아는 것보다 더 강해요.", "pronunciation": "dangsineun aneun geotboda deo ganghaeyo."},
            {"english": "Inner strength comes from within.", "korean": "내면의 힘은 마음에서 나와요.", "pronunciation": "naemyeonui himeun maeumeseo nawayo."},
            {"english": "Challenges make you stronger.", "korean": "도전이 당신을 더 강하게 만들어요.", "pronunciation": "dojeoni dangsineul deo ganghage mandeureoyo."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "korean": "매 순간에서 기쁨을 찾으세요.", "pronunciation": "mae sungan-eseo gippeumeul chajeuseyo."},
            {"english": "Joy is contagious, spread it.", "korean": "기쁨은 전염돼요, 나누세요.", "pronunciation": "gippeumeun jeonyeom-dwaeyo, nanuseyo."},
            {"english": "Dance like nobody's watching.", "korean": "아무도 보지 않는 것처럼 춤추세요.", "pronunciation": "amudo boji anneun geotcheoreom chumchuseyo."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "korean": "삶에서 균형을 찾으세요.", "pronunciation": "salmeseo gyunhyeongeul chajeuseyo."},
            {"english": "Work hard, rest well.", "korean": "열심히 일하고, 잘 쉬세요.", "pronunciation": "yeolsimhi ilhago, jal swiseyo."},
            {"english": "Too much of anything is not good.", "korean": "지나친 것은 부족한 것만 못해요.", "pronunciation": "jinachineun geoseun bujokhan geotman mothaeyo."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "korean": "성장은 안전지대 밖에서 일어나요.", "pronunciation": "seongjangeun anjeonjidae bakkeseo ireonayo."},
            {"english": "Embrace change, grow stronger.", "korean": "변화를 받아들이고, 더 강해지세요.", "pronunciation": "byeonhwareul badadeurigo, deo ganghaejiseyo."},
            {"english": "Every challenge is a chance to grow.", "korean": "모든 도전은 성장의 기회예요.", "pronunciation": "modeun dojeoneun seongjangui gihoeyeyo."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "korean": "당신의 목적을 찾고 따르세요.", "pronunciation": "dangsinui mokjeogeul chajgo ttareuseyo."},
            {"english": "Your life has meaning.", "korean": "당신의 삶에는 의미가 있어요.", "pronunciation": "dangsineui salmeneun uimiga isseoyo."},
            {"english": "Live with intention, not accident.", "korean": "의도적으로 살아가세요, 우연히가 아니라.", "pronunciation": "uidojeogeuro saragaseyo, uyeonhiga anira."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "korean": "지금 이 순간에 집중하세요.", "pronunciation": "jigeum i sungane jipjunghaseyo."},
            {"english": "Breathe deeply, stay grounded.", "korean": "깊게 숨 쉬고, 중심을 잡으세요.", "pronunciation": "gipge sum swigo, jungsimeul jabeuseyo."},
            {"english": "Notice the little things around you.", "korean": "주변의 작은 것들을 주목하세요.", "pronunciation": "jubyeonui jageun geotdeureul jumokhaseyo."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])

    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

def generate_google_tts(text: str, voice_or_lang: str, output_path: str) -> bool:
    """Fallback TTS using Google Translate TTS if Edge TTS fails."""
    import urllib.request
    import urllib.parse

    lang_code = "en"
    voice_lower = str(voice_or_lang).lower()
    if voice_lower.startswith("en"):
        lang_code = "en"
    elif "-" in str(voice_or_lang):
        part = str(voice_or_lang).split("-")[0].lower()
        if part == "zh":
            lang_code = "zh-CN"
        elif part == "fil":
            lang_code = "tl"
        elif part == "nb":
            lang_code = "no"
        else:
            lang_code = part
    else:
        lang_code = voice_lower

    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text:
        return False

    try:
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(clean_text)}&tl={lang_code}&client=tw-ob"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) > 200:
            with open(output_path, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"  Google TTS fallback error ({lang_code}): {e}")
    return False


async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 2):
    """Generate audio using Edge TTS with automatic Google TTS fallback"""
    import edge_tts
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if Path(output_path).exists() and Path(output_path).stat().st_size > 300:
                return True
        except Exception as e:
            if attempt == retries - 1:
                print(f"  Edge TTS notice ({e}), switching to Google TTS fallback...")

    # Fallback to Google TTS
    if generate_google_tts(text, voice, output_path):
        return True

    return False


def generate_all_audio(phrases: list, output_dir: str):
    """Generate audio for all phrases with proper timing"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        korean_file = output_dir / f"korean_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        # Generate English audio
        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        # Generate Korean audio
        cn_success = asyncio.run(generate_single_audio(phrase["korean"], LANG_VOICE, str(korean_file)))
        if not cn_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(korean_file)]
            subprocess.run(cmd, capture_output=True)

        # Get ACTUAL durations
        en_duration = get_audio_duration(str(english_file))
        cn_duration = get_audio_duration(str(korean_file))

        # Add pause between English and Korean
        pause_between = 0.5
        total_duration = en_duration + pause_between + cn_duration

        # Combine audio files
        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(korean_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{korean_file.as_posix()}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "korean": str(korean_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "cn_duration": cn_duration
        })

    print(f"\n[audio] ✓ Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    """Get audio duration in seconds"""
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    """Combine all audio files"""
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")

    concat_file = Path(output_file).parent / "narration_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if concat_file.exists():
        concat_file.unlink()

    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] ✓ Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True

    return False


# ============== IMPROVED BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    """Create Lingexa's exact light cream background"""
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Light cream gradient - NO circles, clean background
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))

    return img



def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    """Generate image with modern glassmorphic UI - Lingexa Inspired"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Load fonts
    english_font_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    korean_font_paths = [
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    # Refined font sizes
    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_korean = load_font(korean_font_paths, 82)
    font_pronunciation = load_font(korean_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    korean = phrase_data.get("korean", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar (Top Left)
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    
    # Badge dimensions - fixed height for perfect centering
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    
    container_x = 60
    container_y = 60
    
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    # Draw text perfectly centered in the badge (with +2px vertical offset for visual balance)
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2), 
        cat_text, 
        fill=(255, 255, 255, 255), 
        font=font_category, 
        anchor="mm"
    )

    # Main Content Area - Center Vertical
    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    # 1. English Box
    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h
    
    # 2. Korean Box
    cn_lines = wrap_text(korean, font_korean, VIDEO_WIDTH - 300)
    cn_line_h = 100
    cn_total_h = len(cn_lines) * cn_line_h
    
    # 3. Pronunciation Box
    py_text = f"[{pronunciation}]"
    py_lines = wrap_text(py_text, font_pronunciation, VIDEO_WIDTH - 400)
    py_line_h = 60
    py_total_h = len(py_lines) * py_line_h

    total_content_h = en_total_h + cn_total_h + py_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    # Draw English Section
    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2
    
    # English Box (Lingexa Dark Purple)
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2), 
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")
    
    y_cursor = y_start + en_box_h + GAP

    # Korean Section (Lingexa Lighter Purple)
    cn_box_h = cn_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + cn_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(cn_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * cn_line_h) + cn_line_h // 2), 
                  line, fill=(255, 255, 255), font=font_korean, anchor="mm")

    y_cursor += cn_box_h + (GAP // 2)

    # Pronunciation Section (Lingexa Peach)
    py_box_h = py_total_h + 40
    py_box_w = box_w - 200
    py_box_x = (VIDEO_WIDTH - py_box_w) // 2
    draw.rounded_rectangle(
        [(py_box_x, y_cursor), (py_box_x + py_box_w, y_cursor + py_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )

    for i, line in enumerate(py_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * py_line_h) + py_line_h // 2), 
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding (Bottom Right)
    brand_text = "VELOCITY KOREAN"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text, 
              fill=(45, 35, 65, 255), font=font_branding)

    # Save
    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path



# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_korean: str, output_path: str):
    """Generate a modern, high-impact thumbnail - Lingexa Inspired"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    # Use the same base background logic but with even more "pop"
    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Load fonts
    english_font_paths = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
    korean_font_paths = ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(korean_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    # Big Impact Title (Dark Purple)
    draw.text((VIDEO_WIDTH // 2, 220), "MASTER KOREAN", fill=(45, 35, 65), font=font_huge, anchor="mm")
    
    # Category Badge (Lingexa Dark Purple)
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    # Korean Translation (Dark Purple)
    draw.text((VIDEO_WIDTH // 2, 530), category_korean, fill=(45, 35, 65), font=font_main, anchor="mm")

    # Features / Call to Action (Lingexa Peach)
    cta_text = "60 ESSENTIAL PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    # Bottom Branding (Dark Purple Bar)
    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY KOREAN", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path



def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    """Extract a frame from the video as thumbnail using FFmpeg"""
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  ✓ Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  ⚠️ Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  ⚠️ Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_korean: str, phrases: list, duration_minutes: float, output_dir: str):
    """Generate viral YouTube title and description with all phrases - COMBINED in one file"""
    
    # Generate viral title variations
    titles = [
        f"Learn Korean in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_korean})",
        f"60 Korean Phrases for {category_english} | Speak Korean Like a Native! ({category_korean})",
        f"Master Korean {category_english} | 60 Essential Korean Phrases with Pronunciation | Velocity Korean",
        f"Korean Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Korean Fluently | {category_english} Phrases | English + Korean + Pronunciation",
    ]

    # Generate comprehensive description
    description = f"""🇰🇷 Learn Korean with Velocity Korean! 🇰🇷

In this video, you'll learn 60 essential Korean phrases about {category_english} ({category_korean}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Korean
• Correct pronunciation with romanization
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    # Add timestamps for each phrase (every 10 phrases grouped)
    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += f"""
📝 ALL PHRASES IN THIS VIDEO:
"""

    # Add all phrases
    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Korean: {phrase['korean']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += f"""
🎯 PERFECT FOR:
• Korean beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Korean language
• Language enthusiasts and polyglots
• Students preparing for TOPIK exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Korean learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY KOREAN:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Korean Motivation Phrases
• Korean Love Expressions
• TOPIK 1 Vocabulary
• Basic Korean Greetings

#LearnKorean #KoreanPhrases #KoreanLanguage #{category_english.replace(' ', '')} #VelocityKorean #KoreanForBeginners #SpeakKorean #KoreanVocabulary #Pronunciation #LanguageLearning #Korean101 #KoreanLesson

---
© Velocity Korean - Making Korean learning accessible to everyone!
"""

    # Write to COMBINED file (title + description in one)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Combined YouTube upload file (title + description)
    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("📌 RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📝 SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("📄 VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("🏷️ VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Korean",
            "Korean Phrases",
            "Korean Language",
            category_english,
            "Velocity Korean",
            "Korean for Beginners",
            "Speak Korean",
            "Korean Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Korean 101",
            "Korean Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    # Metadata JSON (for easy parsing)
    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_korean": category_korean,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] ✓ Generated YouTube upload files")
    print(f"  📄 youtube_upload_info.txt (title + description + tags)")
    print(f"  📄 video_metadata.json")

    return metadata


# ============== VIDEO CREATION WITH TRANSITIONS ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    """Create video from images and audio with PERFECT synchronization"""

    print(f"\n[video] Creating long-form video from {len(image_files)} images...")
    print(f"[video] Embedding audio in each clip for frame-perfect sync...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s (EN: {audio_info.get('en_duration', 0):.1f}s + CN: {audio_info.get('cn_duration', 0):.1f}s)")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] ✓ Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    """Generate complete long-form YouTube video with thumbnail and metadata"""

    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    # Use provided phrases count or default
    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"🎬 LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_KOREAN[category_english]})")
    print(f"🎯 Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    # Step 1: Generate unique phrases
    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} → {phrase['korean']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    # Step 2: Generate images
    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    # Step 3: Generate thumbnail
    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_KOREAN[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_KOREAN[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    # Calculate actual duration
    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    # Step 5: Create video
    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )
    
    # Extract video frame as thumbnail
    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    # Step 6: Generate title and description
    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_KOREAN[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    metadata = {
        "category_english": category_english,
        "category_korean": CATEGORIES_KOREAN[category_english],
        "timestamp": timestamp,
        "target_phrases": phrases_count,
        "actual_duration_seconds": total_duration,
        "actual_duration_minutes": total_duration / 60,
        "phrases_count": len(phrases),
        "phrases": phrases,
        "video": str(output_video),
        "audio": str(final_audio),
        "thumbnail": str(thumbnail_path),
        "resolution": f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "fps": FPS
    }

    with open(video_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    # Save latest video info for upload script (BEFORE metadata overwrite)
    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Korean: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Korean", "Korean Phrases", "Korean", category_english, "Velocity Korean"],
        "category_english": category_english,
        "category_korean": CATEGORIES_KOREAN[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)


    print(f"\n{'='*80}")
    print(f"✅ LONG-FORM VIDEO COMPLETE!")
    print(f"  📁 {video_dir}")
    print(f"  🎬 {output_video.name}")
    print(f"  🖼️  thumbnail.jpg (generated)")
    print(f"  🖼️  {video_thumbnail_path.name} (from video)")
    print(f"  📄 youtube_upload_info.txt (title + description + tags)")
    print(f"  ⏱️  Duration: {total_duration/60:.2f} minutes")
    print(f"  📊 Phrases: {len(phrases)}")
    print(f"  🏷️  Branding: Velocity Korean")
    print(f"  📺 Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return metadata


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    """Generate multiple long-form videos"""
    print(f"\n🎬 Generating {count} long-form video(s)...")
    print("="*80)

    for i in range(count):
        print(f"\n{'='*80}")
        print(f"🎬 VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)

    print("\n" + "="*80)
    print(f"✅ ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Korean YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate (determines video length, ~5.5s per phrase. 60 phrases = ~5.5 mins)")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate (e.g. 'Motivation', 'Friendship'). Random if not provided.")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("🇰🇷 VELOCITY KOREAN - YOUTUBE LONG-FORM AUTOMATION 🇰🇷")
    print("="*80)
    print("\n✨ FEATURES:")
    print("  ✓ 16:9 format (1920x1080) for YouTube long-form")
    print(f"  ✓ Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  ✓ Lingexa Light Theme (Cream background, dark/light purple + peach containers)")
    print("  ✓ Natural pauses with commas (non-robotic TTS)")
    print("  ✓ Perfect audio-video synchronization")
    print("  ✓ Smooth crossfade transitions")
    print("  ✓ NEVER repeats phrases (permanent history tracking)")
    print(f"\n📊 AVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_KOREAN[cat]})")
    print(f"\n📈 VIDEO SPECIFICATIONS:")
    print(f"  • Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  • Frame Rate: {FPS} FPS")
    print(f"  • Target Phrases: {args.phrases}")
    print(f"  • Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  • Phrase History: PERMANENT (never deletes)")
    print("="*80)

    # Note: History tracking is built-in. Check output/history/all_generated_phrases.json
    generate_longform_video(category_english=args.category, target_phrases=args.phrases)