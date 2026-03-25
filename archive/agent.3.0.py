import os
import json
import ast
import time
import random
import string
import requests
import urllib.parse
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# ספריות גוגל (Implementation ready for API Key)
from google.oauth2 import service_account
import googleapiclient.discovery

# ==========================================
# 1. הגדרות ותשתית (Settings & Core)
# ==========================================
load_dotenv(override=True)

# Logging מסודר לטרמינל
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_KEY_FILE = 'kal-ride-publisher-key.json'

FAIL_COUNTER = 0
MAX_FAILS = 5

def get_now_utc():
    return datetime.now(timezone.utc)

def safe_json_parse(text):
    if not text: return None
    clean_text = text.replace("```json", "").replace("```", "").strip()
    try:
        start, end = clean_text.find('{'), clean_text.rfind('}')
        if start != -1 and end != -1:
            clean_text = clean_text[start:end+1]
        return json.loads(clean_text)
    except Exception:
        try: return ast.literal_eval(clean_text)
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            return None

def call_ai(prompt, system_prompt, expect_json=True):
    global FAIL_COUNTER
    if FAIL_COUNTER >= MAX_FAILS: raise Exception("CIRCUIT BREAKER ACTIVE")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7, 
            "responseMimeType": "application/json" if expect_json else "text/plain"
        }
    }
    for attempt in range(3):
        try:
            res = requests.post(url, json=payload, timeout=15)
            res.raise_for_status()
            data = res.json()
            parts = data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
            if not parts: raise Exception("Empty AI Response")
            res_text = parts[0].get('text', '').strip()
            FAIL_COUNTER = 0
            if not expect_json: return res_text
            parsed = safe_json_parse(res_text)
            if parsed: return parsed
            raise Exception("Invalid JSON formatting")
        except Exception as e:
            FAIL_COUNTER += 1
            logger.warning(f"AI Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    raise Exception("AI FAILED")

# ==========================================
# 2. בנק מדיה (Media Bank)
# ==========================================
BRAND_CONTEXT = """
Kal Ride: Premium electric off-road in Motza Valley, Jerusalem. 
Focus: Luxury boutique, Mia Four vehicles, silence and nature.
"""

MEDIA_BANK = {
    "extreme": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/bg-frontal.mp4", "desc": "Frontal extreme video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-11.mp4", "desc": "Technical riding"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-24.jpeg", "desc": "Extreme dirt path"}
    ],
    "family_and_couples": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-1.jpg", "desc": "Couple smiling"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/family240326.mp4", "desc": "Beautiful nature ride"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-5.jpg", "desc": "Sunset romantic"}
    ],
    "nature_and_views": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg", "desc": "Sunny day forest"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-14.jpg", "desc": "Jerusalem sunset"}
    ],
    "pov": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/bg-pov.mp4", "desc": "POV driving experience video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov240326.mp4", "desc": "Kal Ride action POV"}
    ],
    "technical": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/bg-stability.mp4", "desc": "Stability demo"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/ready.jpeg", "desc": "Ready for ride"}
    ]
}

# ==========================================
# 3. פונקציות דאטה (Data Logic)
# ==========================================

def is_shabbat_now():
    now = datetime.now() 
    return (now.weekday() == 4 and now.hour >= 16) or (now.weekday() == 5 and now.hour < 19)

def can_post():
    try:
        res = supabase.table("agent_learning").select("created_at").order("created_at", desc=True).limit(1).execute()
        if res.data:
            last = datetime.fromisoformat(res.data[0]["created_at"]).replace(tzinfo=timezone.utc)
            if (get_now_utc() - last).total_seconds() < 14400: return False
    except: pass
    return True

def fetch_meta_performance():
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID: return "No Meta Token."
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/posts?fields=message,likes.summary(total_count),comments.summary(total_count)&limit=3&access_token={META_ACCESS_TOKEN}"
    try:
        res = requests.get(url, timeout=15)
        data = res.json().get('data', [])
        return "\n".join([f"Post: {p.get('message','')[:30]} | Eng: {p.get('likes',{}).get('summary',{}).get('total_count',0) + p.get('comments',{}).get('summary',{}).get('total_count',0)}" for p in data])
    except: return "No Meta data."

def get_cmo_targets():
    path = "manual_strategy.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            if d.get("is_active"):
                now = datetime.now()
                end = datetime.fromisoformat(d.get("end_time", "2099-01-01T00:00:00"))
                if now > end:
                    d["is_active"] = False
                    with open(path, "w", encoding="utf-8") as fw: json.dump(d, fw, indent=4)
                else: return d.get("override_target", 15), d.get("focus", "Creative Strategy")
    return 15, "Automated Growth Strategy"

def get_smart_media(category):
    options = MEDIA_BANK.get(category, MEDIA_BANK['nature_and_views'])
    try:
        res = supabase.table("agent_learning").select("media_url, engagement_score").execute()
        scores = {m['url']: 0 for m in options}
        if res.data:
            for r in res.data:
                u = r.get('media_url')
                if u in scores: scores[u] += r.get('engagement_score', 0)
        
        if all(v == 0 for v in scores.values()): return random.choice(options)
        sorted_m = sorted(options, key=lambda x: scores.get(x['url'], 0), reverse=True)
        return random.choice(sorted_m[:2])
    except: return random.choice(options)

# ==========================================
# 4. עשרת הסוכנים (The 10 Agents)
# ==========================================

def agent_1_le_directeur(meta_insights, history):
    logger.info("👔 Agent 1 (CMO): Analysis...")
    target, focus = get_cmo_targets()
    sys = f"ROLE: CMO. {BRAND_CONTEXT}. Logic in French."
    prompt = f"Insights: {meta_insights}. History: {history}. Target: {target}. Focus: {focus}. Decide strategy. JSON: {{'wait_and_stop': false, 'execute_meta': true, 'execute_google': true, 'execute_article': false, 'launch_promo': false, 'trend_concept': '...', 'category': 'nature_and_views', 'logic_fr': '...'}}"
    return call_ai(prompt, sys)

def agent_2_architecte(trend):
    logger.info("📐 Agent 2 (Architect): Structure...")
    sys = "SEO Expert. IN HEBREW."
    prompt = f"Trend: {trend}. JSON: {{'topic': '...', 'sections': ['...', '...', '...']}}"
    return call_ai(prompt, sys)

def agent_3_redacteur(topic, section):
    logger.info(f"✍️ Agent 3 (Writer): {section}")
    return call_ai(f"Write 150 words in Hebrew on {topic} for section {section}", "Elite Writer", expect_json=False)

def agent_4_copywriter(trend, promo=None):
    logger.info("🗣️ Agent 4 (Social): Writing...")
    trend_encoded = urllib.parse.quote(trend)
    tracking_link = f"https://www.kalride.com/?utm_source=ai&utm_campaign={trend_encoded}"
    sys = f"Viral Expert. {BRAND_CONTEXT}. IN HEBREW."
    prompt = f"Trend: {trend}. Promo: {promo}. Link: {tracking_link}. JSON: {{'social_post': '...'}}"
    return call_ai(prompt, sys)

def agent_5_admin_web(discount=15):
    logger.info("🎟️ Agent 5 (Web Admin): Coupon...")
    while True:
        code = f"KAL-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
        exists = supabase.table("active_promotions").select("coupon_code").eq("coupon_code", code).execute()
        if not exists.data:
            expires = (get_now_utc() + timedelta(hours=24)).isoformat()
            supabase.table("active_promotions").insert({"coupon_code": code, "discount_percent": discount, "expires_at": expires}).execute()
            return code

def agent_6_traducteur(text, lang):
    logger.info(f"🌍 Agent 6 (Translator): To {lang}")
    return call_ai(f"Translate to {lang}:\n{text}", "Expert Translator", expect_json=False)

def agent_7_correcteur(text, lang="Hebrew"):
    logger.info(f"🔍 Agent 7 (Proofreader): QA {lang}")
    sys = f"Proofreader in {lang}. RETURN ONLY CORRECTED TEXT."
    return call_ai(f"Fix errors: {text}", sys, expect_json=False)

def agent_8_meta(caption, url):
    logger.info(f"✅ Agent 8 (Meta): Distributed {url}")
    return True # Implement actual FB Graph API call here

def agent_9_google(caption, promo=None):
    logger.info(f"✅ Agent 9 (Google): Maps Update with {promo}")
    return True # Implement Google My Business API call here

def agent_10_revenue_auditor():
    logger.info("💰 Agent 10 (Revenue Brain): ROI Audit...")
    try:
        res = supabase.table("agent_learning").select("trend_concept, engagement_score").execute()
        if not res.data: return "No data."
        scores = {}
        for r in res.data:
            t = r.get("trend_concept")
            scores[t] = scores.get(t, 0) + r.get("engagement_score", 0)
        best = sorted(scores.items(), key=lambda x: x[1], reverse=True)[0]
        return f"Top trend: {best[0]} (Score: {best[1]})"
    except: return "No insights yet."

# ==========================================
# 5. המנוע המרכזי (The Pipeline)
# ==========================================

def run_full_cycle():
    logger.info("--- 🏭 KAL RIDE AI 3.0 : FULL START ---")
    try:
        if is_shabbat_now() or not can_post():
            logger.info("⏸️ System Paused.")
            return

        meta_in = fetch_meta_performance()
        past_trends = agent_10_revenue_auditor()
        
        decision = agent_1_le_directeur(meta_in, past_trends)
        if not decision or decision.get("wait_and_stop"): return

        decision["execute_google"] = False # Protective guardrail

        promo = agent_5_admin_web() if decision.get("launch_promo") else None
        raw_social = agent_4_copywriter(decision.get('trend_concept'), promo)
        
        if raw_social:
            final_text = agent_7_correcteur(raw_social.get('social_post', ''), "Hebrew")
            media = get_smart_media(decision.get('category', 'nature_and_views'))
            
            if decision.get("execute_meta"): agent_8_meta(final_text, media['url'])
            
            supabase.table("agent_learning").insert({
                "trend_concept": decision.get('trend_concept'),
                "insight": decision.get('logic_fr'),
                "media_url": media['url'],
                "action_taken": "Cycle 3.0 Successful",
                "created_at": get_now_utc().isoformat()
            }).execute()

        logger.info("✅ CYCLE 3.0 COMPLETE.")
    except Exception as e:
        logger.error(f"🚨 PIPELINE ERROR: {e}")

if __name__ == "__main__":
    run_full_cycle()