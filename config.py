"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY KOREAN"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "KOREAN"
HANDLE = "@velocitykorean"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'ko',
 'name': 'Korean',
 'native_name': '한국어',
 'history_key': 'korean',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'ko-KR-SunHiNeural',
 'native_fallback_voice': 'ko-KR-InJoonNeural',
 'native_engine': 'edge',
 'native_lang_code': 'ko',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': '한국어',
 'translit_label': 'ROMANIZED',
 'flag': 'kr',
 'greeting': '안녕하세요!',
 'encouragement': '훌륭해요!',
 'rtl': False,
 'char_tiles': True,
 'script_font': 'Script.ttf',
 'glyphs': '가나다라마바사아자차카타파하한국어매일공부'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': '동기',
 'Love': '사랑',
 'Success': '성공',
 'Wisdom': '지혜',
 'Happiness': '행복',
 'Self Improvement': '자기계발',
 'Gratitude': '감사',
 'Friendship': '우정',
 'Hope': '희망',
 'Creativity': '창의성',
 'Inner Peace': '내면의 평화',
 'Confidence': '자신감',
 'Perseverance': '인내',
 'Inspiration': '영감',
 'Positive Life': '긍정적인 삶',
 'Courage': '용기',
 'Kindness': '친절',
 'Patience': '인내심',
 'Forgiveness': '용서',
 'Strength': '힘',
 'Joy': '기쁨',
 'Balance': '균형',
 'Growth': '성장',
 'Purpose': '목적',
 'Mindfulness': '마음챙김',
 'Travel & Airport': '여행 및 공항',
 'Ordering Food & Dining': '음식 주문 및 식사',
 'Shopping & Prices': '쇼핑 및 가격',
 'Asking for Directions': '길 묻기',
 'Hotel & Accommodation': '호텔 및 숙박',
 'Daily Routine': '일상생활',
 'Meeting People & Greetings': '사람 만나기 및 인사',
 'Emergency & Health': '응급 상황 및 건강',
 'Public Transportation': '대중교통',
 'Work & Office': '업무 및 사무실',
 'Weather & Small Talk': '날씨 및 가벼운 대화',
 'Coffee Shop & Bakery': '커피숍 및 베이커리',
 'Family & Home': '가족 및 집',
 'Hobbies & Free Time': '취미 및 여가',
 'Dating & Romance': '데이트 및 연애',
 'Phone Calls & Messages': '전화 통화 및 메시지',
 'Banking & Money': '은행 및 돈',
 'Doctor & Pharmacy': '의사 및 약국',
 'Sports & Fitness': '스포츠 및 피트니스',
 'Celebrations & Parties': '축하 및 파티',
 'Feelings & Emotions': '감정 및 느낌',
 'Agreeing & Disagreeing': '동의 및 반대',
 'Making Plans': '계획 세우기',
 'Common Native Slang': '자주 쓰이는 원어민 은어',
 'Cultural Traditions': '문화 전통'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnkorean',
 '#koreanlessons',
 '#koreanforbeginners',
 '#languagelearning',
 '#koreanvocabulary',
 '#velocitykorean',
 '#dailykorean',
 '#korean',
 '#learnlanguages',
 '#speakkorean']
# ==== HASHTAGS END ====
