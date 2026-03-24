import os
import json
import random
import time
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# ==========================================
# 1. אתחול, הגדרות ובסיס נתונים
# ==========================================
load_dotenv(override=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") 
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID")
INSTAGRAM_BUSINESS_ID = os.environ.get("INSTAGRAM_BUSINESS_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==========================================
# 2. קונטקסט ובנק המדיה המלא
# ==========================================
BRAND_CONTEXT = """
BRAND CONTEXT:
- "Kal Ride" offers premium, quiet electric off-road experiences in Motza Valley, Jerusalem.
- Vehicles: "Mia Four" (Electric, stable, high-end).
- CAPACITY: Boutique fleet of 5 vehicles. For larger groups, custom solutions.
- SCHEDULE: Sun-Thu full day, Friday until afternoon. Closed on Shabbat/Holidays.
- STRATEGY: High-end luxury, boutique feel, focus on nature and off-road stability.
"""

MEDIA_BANK = {
    "extreme": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/bg-frontal.mp4", "desc": "Frontal extreme video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-11.mp4", "desc": "Technical riding"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-9.webp", "desc": "Mia Four high mountains"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-24.jpeg", "desc": "Extreme dirt path"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/extreme/kalride-21.webp", "desc": "Riding through clouds"}
    ],
    "family_and_couples": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-1.jpg", "desc": "Couple smiling"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-2.jpg", "desc": "Group of friends"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-4.jpg", "desc": "Arazim valley nature"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-5.jpg", "desc": "Sunset romantic"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/tour-6.jpg", "desc": "Relaxed nature break"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-30.jpeg", "desc": "Clean vehicles ready"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/family240326.mp4", "desc": "Beautiful nature ride"}
    ],
    "nature_and_views": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg", "desc": "Sunny day forest"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/family/karide-29.jpeg", "desc": "Panoramic view"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/route-110.jpeg", "desc": "Scenic route"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-14.jpg", "desc": "Jerusalem sunset"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/tour-15.jpg", "desc": "Hidden springs"}
    ],
    "pov": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/bg-pov.mp4", "desc": "POV driving experience video"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov240326.mp4", "desc": "Kal Ride action POV"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/pov/pov.jpeg", "desc": "POV driver perspective"}
    ],
    "technical": [
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/bg-stability.mp4", "desc": "Vehicle stability demonstration"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-13.webp", "desc": "Technical terrain"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-21.webp", "desc": "Technical ride details"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-22.jpeg", "desc": "Technical maneuver"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-25.jpeg", "desc": "Technical off-road"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-27.jpeg", "desc": "Vehicle capabilities"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/kalride-28.jpeg", "desc": "Advanced terrain"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/ready.jpeg", "desc": "Vehicle ready for ride"},
        {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/technical/specs.webp", "desc": "Mia Four specifications"}
    ]
}

# ==========================================
# 3. פונקציות תשתית ולמידה
# ==========================================

def log_error(msg):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {msg}\n")

def is_shabbat_now():
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    if (weekday == 4 and hour >= 15) or (weekday == 5 and hour < 19): return True
    return False

def extract_json(text):
    start, end = text.find('{'), text.rfind('}')
    return text[start:end+1] if (start != -1 and end != -1) else text

def fetch_meta_insights():
    """ הפונקציה החדשה שקוראת נתונים ממטא כדי ללמוד מהשטח """
    if not META_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        return "No Meta Token available to fetch insights."
    
    # שולף את 3 הפוסטים האחרונים כולל כמות לייקים ותגובות
    url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/posts?fields=id,message,created_time,comments.summary(total_count),likes.summary(total_count)&limit=3&access_token={META_ACCESS_TOKEN}"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        posts = res.json().get('data', [])
        
        insights = []
        for p in posts:
            likes = p.get('likes', {}).get('summary', {}).get('total_count', 0)
            comments = p.get('comments', {}).get('summary', {}).get('total_count', 0)
            date = p.get('created_time', '')[:10]
            msg = p.get('message', '')[:40].replace('\n', ' ')
            insights.append(f"[{date}] Post: '{msg}...' | Likes: {likes} | Comments: {comments}")
            
        return "\n".join(insights) if insights else "No recent posts found on the page."
    except Exception as e:
        log_error(f"Failed to fetch Meta insights: {e}")
        return "Failed to fetch recent performance."

def call_ai(prompt, system_prompt, expect_json=True, max_retries=3):
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }

    if expect_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🤖 AI Call (attempt {attempt})...")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "candidates" not in data:
                raise Exception(f"No candidates in response: {data}")

            res_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            if not expect_json: return res_text

            def clean_json(text):
                text = re.sub(r'[\x00-\x1F]+', ' ', text)
                start, end = text.find('{'), text.rfind('}')
                if start != -1 and end != -1: return text[start:end+1]
                return text

            cleaned = clean_json(res_text)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return json.loads(cleaned.replace("'", '"'))

        except requests.exceptions.Timeout:
            log_error(f"⏱️ Timeout on attempt {attempt}")
        except requests.exceptions.HTTPError as e:
            err_msg = f"❌ HTTP Error: {e}. Response: {response.text}"
            log_error(err_msg)
            if response.status_code in [401, 403, 404]:
                raise Exception("🚨 Fatal API Error – check API key / model")
        except Exception as e:
            log_error(f"❌ General Error on attempt {attempt}: {e}")
        time.sleep(2)

    raise Exception("🚨 AI FAILED after retries")

def post_to_meta(caption, media_url):
    if not META_ACCESS_TOKEN: 
        print("⚠️ Meta Token missing. Cannot publish.")
        return
    
    is_video = media_url.lower().endswith('.mp4')
    print(f"🔗 Publishing Media URL: {media_url}")
    
    # --- Facebook Publishing ---
    if FACEBOOK_PAGE_ID:
        print(f"🚀 Publishing to Facebook (Video: {is_video})...")
        if is_video:
            fb_url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/videos"
            fb_payload = {"file_url": media_url, "description": caption, "access_token": META_ACCESS_TOKEN}
        else:
            fb_url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/photos"
            fb_payload = {"url": media_url, "message": caption, "access_token": META_ACCESS_TOKEN}
        
        try:
            fb_res = requests.post(fb_url, data=fb_payload)
            fb_res.raise_for_status()
            print("✅ Published to Facebook!")
        except requests.exceptions.HTTPError as err:
            print(f"❌ Facebook Publish Failed: {fb_res.text}")

    # --- Instagram Publishing ---
    if INSTAGRAM_BUSINESS_ID:
        print(f"🚀 Publishing to Instagram (Video: {is_video})...")
        ig_media_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media"
        ig_payload = {"caption": caption, "access_token": META_ACCESS_TOKEN}
        
        if is_video:
            ig_payload["media_type"] = "REELS"
            ig_payload["video_url"] = media_url
        else:
            ig_payload["image_url"] = media_url
            
        try:
            creation_res = requests.post(ig_media_url, data=ig_payload)
            creation_res.raise_for_status()
            container_id = creation_res.json().get("id")
            
            print("⏳ Waiting 10s for Instagram media processing...")
            time.sleep(10)
            
            ig_publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
            publish_payload = {"creation_id": container_id, "access_token": META_ACCESS_TOKEN}
            publish_res = requests.post(ig_publish_url, data=publish_payload)
            publish_res.raise_for_status()
            print("✅ Published to Instagram!")
        except requests.exceptions.HTTPError as err:
            print(f"❌ Instagram Publish Failed")
            if 'creation_res' in locals(): print(creation_res.text)

# ==========================================
# 4. הסוכנים האוטונומיים
# ==========================================

def get_macro_learning():
    try:
        res = supabase.table("agent_learning").select("trend_concept").order("created_at", desc=True).limit(1).execute()
        if res.data:
            return res.data[0]['trend_concept']
    except Exception as e:
        log_error(f"Macro Learning fetch failed: {e}")
    return "No previous data"

def agent_0_challenger(last_trend, meta_insights):
    print("🧠 Agent 0 (CMO): Analyzing Real-Time Meta Data & Strategy...")
    sys = f"ROLE: Aggressive CMO & Data Analyst. {BRAND_CONTEXT}. KPI: Maximum Conversions without Spamming."
    
    # הפרומפט החדש שעושה את הקסם ומנתח את פייסבוק
    prompt = f"""You are the CMO of Kal Ride.
    RECENT FACEBOOK POSTS PERFORMANCE:
    {meta_insights}
    
    LAST GENERATED TREND: '{last_trend}'
    
    YOUR TASK:
    Analyze the recent performance. If a post was made today or is gaining heavy traction, YOU MUST select 'wait' to avoid spamming the audience.
    If it's time for new content, invent a completely NEW marketing trend, or 'repurpose' an older winning idea.
    'article_only' or 'both' should be used RARELY (only for deep-dive SEO).
    
    The values for 'trend_concept' and 'logic' MUST be in Hebrew.
    Output JSON: {{
        "trend_concept": "...", 
        "logic": "Explain why you chose to wait, repurpose, or create new based on the data...", 
        "action_type": "wait" OR "repurpose" OR "post_only" OR "article_only" OR "both",
        "category": "extreme/family_and_couples/nature_and_views/pov/technical"
    }}"""
    try:
        return call_ai(prompt, sys, expect_json=True)
    except Exception as e:
        print(f"🚨 Agent 0 FAILED: {e}")
        return None

def agent_1_strategist(trend):
    print(f"🎯 Agent 1 (Strategist): Planning for trend '{trend.get('trend_concept', '')}'")
    sys = f"Lead SEO Strategist. {BRAND_CONTEXT}"
    prompt = f"Trend: {trend}. Create topic and angle EXCLUSIVELY IN HEBREW. Create slug in English. Output JSON: {{topic: 'נושא בעברית', angle: 'זווית בעברית', slug: 'english-slug'}}"
    try: return call_ai(prompt, sys, expect_json=True)
    except Exception: return None

def agent_2_architect(strategy):
    print("📐 Agent 2 (Architect): Designing article structure...")
    sys = f"Content Architect. {BRAND_CONTEXT}"
    prompt = f"Topic: {strategy.get('topic')}. Create exactly 4 section titles IN HEBREW ONLY. Output JSON: {{sections: ['כותרת 1', 'כותרת 2', 'כותרת 3', 'כותרת 4']}}"
    try: return call_ai(prompt, sys, expect_json=True)
    except Exception: return None

def agent_3_writer(title, section, prev_text):
    print(f"✍️ Agent 3 (Writer): Writing section '{section}'")
    sys = f"Elite SEO Writer. {BRAND_CONTEXT}. CRITICAL: Write EXCLUSIVELY IN HEBREW."
    prompt = f"Article Topic: {title}. Section: {section}. Write 150 words based on the context in pure, natural Hebrew."
    try: return call_ai(prompt, sys, expect_json=False)
    except Exception: return None

def agent_4_finisher(title, body):
    print("🎀 Agent 4 (Finisher): Writing Intro & Outro...")
    sys = f"Editor in Chief. {BRAND_CONTEXT}. CRITICAL: WRITE IN HEBREW ONLY."
    prompt = f"Article Title: {title}. Write an engaging intro and a strong CTA outro EXCLUSIVELY IN HEBREW. Output JSON: {{intro: 'פתיח...', outro: 'סיום...'}}"
    try: return call_ai(prompt, sys, expect_json=True)
    except Exception: return None

def agent_5_translator(text, target_lang):
    print(f"🌍 Agent 5 (Translator): Translating to {target_lang}...")
    sys = "Expert high-end translator. Keep the luxury tone intact."
    prompt = f"Translate the following text to {target_lang}:\n\n{text}"
    try: return call_ai(prompt, sys, expect_json=False)
    except Exception: return None

def agent_6_social(topic, trend):
    print("📸 Agent 6 (Social): Creating viral post with website link...")
    sys = f"Viral Social Media Manager. {BRAND_CONTEXT}"
    # הוספת דרישה לקישור בסוף הפוסט
    prompt = f"""Topic/Trend: {topic}. 
    Write a short, exciting Instagram/Facebook caption in Hebrew with emojis.
    CRITICAL: Always end the post with a call to action and this link: https://www.kalride.com
    Output JSON: {{ "social_post": "טקסט הפוסט..." }}"""
    try: return call_ai(prompt, sys, expect_json=True)
    except Exception: return None

def agent_7_proofreader(text, lang):
    print(f"🔍 Agent 7 (Proofreader): Polishing {lang} text...")
    sys = f"ROLE: Expert Proofreader in {lang}. FIX ALL SPELLING/GRAMMAR. Return ONLY corrected text."
    try: return call_ai(f"Fix this text: {text}", sys, expect_json=False)
    except Exception: return text

# ==========================================
# 5. הניתוב האסטרטגי
# ==========================================

def run_full_cycle():
    print("--- 🏭 KAL RIDE AUTONOMOUS MARKETING STARTED ---")
    
    # למידת מקרו (היסטוריה) ולמידת מיקרו (זמן אמת מפייסבוק)
    last_trend = get_macro_learning()
    meta_insights = fetch_meta_insights()
    
    trend = agent_0_challenger(last_trend, meta_insights)
    if not trend:
        print("🚨 STOP: Agent 0 failed. Stopping pipeline.")
        return

    action_type = trend.get('action_type', 'wait')
    print(f"🤖 CMO Logic: {trend.get('logic', 'No logic provided')}")
    print(f"🤖 CMO Decision: We will execute -> {action_type.upper()}")
    
    # אם ה-CMO החליט להמתין כדי לא להספים
    if action_type == 'wait':
        print("⏸️ CMO decided to wait and let current content grow. Exiting cycle gracefully.")
        try:
            supabase.table("agent_learning").insert({
                "trend_concept": "WAIT & OBSERVE",
                "insight": trend.get('logic', 'Avoiding spam.'),
                "action_taken": "Action: WAIT. No post generated.",
                "created_at": datetime.now().isoformat()
            }).execute()
        except Exception as e: pass
        return

    topic_hebrew = trend.get('trend_concept', 'חוויית שטח במוצא')

    # מסלול מאמר כולל תרגומים
    if action_type in ['article_only', 'both']:
        strat = agent_1_strategist(trend)
        if strat:
            topic_hebrew = strat.get('topic', topic_hebrew)
            structure = agent_2_architect(strat)
            if structure:
                sections = structure.get('sections', ["מבוא", "החוויה", "הטבע", "סיכום"])
                raw_body = ""
                for sec in sections:
                    section_content = agent_3_writer(topic_hebrew, sec, raw_body)
                    if section_content: raw_body += f"<h2>{sec}</h2>\n" + section_content + "\n\n"
                
                finishing = agent_4_finisher(topic_hebrew, raw_body)
                if finishing:
                    full_hebrew_article = f"{finishing.get('intro', '')}\n\n{raw_body}\n\n{finishing.get('outro', '')}"
                    clean_hebrew_article = agent_7_proofreader(full_hebrew_article, "Hebrew")
                    
                    raw_english = agent_5_translator(clean_hebrew_article, "English")
                    if raw_english: 
                        agent_7_proofreader(raw_english, "English")
                        print("📝 English translation & proofreading complete.")
                        
                    raw_french = agent_5_translator(clean_hebrew_article, "French")
                    if raw_french: 
                        agent_7_proofreader(raw_french, "French")
                        print("📝 French translation & proofreading complete.")
                    print("✅ Article generation complete.")
    elif action_type != 'wait':
        print("⏭️ CMO selected to skip article generation.")

    # מסלול סושיאל ופרסום
    if action_type in ['post_only', 'both', 'repurpose']:
        social_content = agent_6_social(topic_hebrew, trend)
        if social_content:
            clean_caption = agent_7_proofreader(social_content.get('social_post', 'יוצאים לשטח!'), "Hebrew")
            cat = trend.get('category', 'nature_and_views')
            media_options = MEDIA_BANK.get(cat, MEDIA_BANK['nature_and_views'])
            
            valid_media = [m for m in media_options if not m['url'].lower().endswith('.webp')]
            if not valid_media:
                selected_media = {"url": "https://jnkcqijbbotalymmyjay.supabase.co/storage/v1/object/public/pov/nature/summday_9665585533.jpg"}
            else:
                selected_media = random.choice(valid_media)
            
            if not is_shabbat_now():
                post_to_meta(clean_caption, selected_media['url'])
            else:
                print("⏸️ Shabbat Mode: Publishing paused.")

    # שמירה לדאשבורד
    try:
        supabase.table("agent_learning").insert({
            "trend_concept": trend.get('trend_concept', 'Boutique Eco-Luxury'),
            "insight": trend.get('logic', 'Strategy applied successfully'),
            "action_taken": f"Action: {action_type}. Topic: {topic_hebrew}",
            "created_at": datetime.now().isoformat()
        }).execute()
        print("💾 Pipeline execution saved to Supabase Memory.")
    except Exception as e:
        print(f"⚠️ Supabase Save Error: {e}")
        log_error(f"Supabase Save Error: {e}")
        
    print("✅ CYCLE COMPLETE.")

if __name__ == "__main__":
    run_full_cycle()