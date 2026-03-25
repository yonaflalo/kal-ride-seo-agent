import os
import json
import uuid
import time
import logging
import re
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client
from google import genai
from google.genai import types

# ==========================================
# 1. INIT
# ==========================================
load_dotenv(override=True)

def now_utc():
    return datetime.now(timezone.utc)

def get_env(key):
    return (os.environ.get(key) or "").strip()

GEMINI_KEY   = get_env("GEMINI_API_KEY")
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_SERVICE_ROLE_KEY")

if not GEMINI_KEY or not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Missing ENV variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_KEY)

MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAL-RIDE-V6] - %(message)s')
logger = logging.getLogger(__name__)

BRAND_CONTEXT = "קל רייד (Kal Ride) - חוויית שטח חשמלית פרימיום בעמק מוצא בירושלים. רכבי Mia Four."

# חוק הברזל - טלפון העסק בפורמט בינלאומי ללינקים
BUSINESS_PHONE = "972534853699"

# ==========================================
# 2. BULLETPROOF AI CORE
# ==========================================
def safe_json_parse(text):
    if not text: return None
    try: return json.loads(text)
    except:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try: return json.loads(match.group())
            except: return None
    return None

def call_ai(prompt, sys, expect_json=True):
    for model in MODELS:
        try:
            res = ai_client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys,
                    response_mime_type="application/json" if expect_json else "text/plain"
                )
            )
            text = res.text.strip() if res.text else ""
            if not text: continue
            
            if not expect_json: return text
            parsed = safe_json_parse(text)
            if parsed: return parsed
        except Exception as e:
            logger.debug(f"AI fail {model}: {e}")
            continue
    return None

# ==========================================
# 3. KEYWORD & MATRIX ENGINE
# ==========================================
def generate_keywords():
    base = [
        "טיול שטח ירושלים",
        "אטרקציות בירושלים",
        "טיול טרקטורונים חשמליים",
        "אטרקציות אקסטרים בישראל"
    ]
    kws = []
    for b in base:
        kws.append(b)
        kws.append(b + " למשפחות")
        kws.append("המלצות " + b)
    return list(set(kws))

def get_best_angle():
    return "extreme"

# ==========================================
# 4. CONTENT GENERATION (WITH SEO ARMOR)
# ==========================================
def get_internal_links():
    try:
        res = supabase.table("articles").select("slug, title_he").limit(3).execute()
        if not res or not res.data: return ""
        html = "<h3>עוד חוויות שטח מומלצות:</h3><ul>"
        for r in res.data:
            html += f"<li><a href='/blog/{r['slug']}'>{r.get('title_he', 'קרא עוד')}</a></li>"
        html += "</ul>"
        return html
    except: return ""

def generate_article(keyword, angle):
    topic = f"{keyword} - סגנון: {angle}"
    logger.info(f"🧠 Création de l'article pour : {topic}")

    # 1. HEADINGS (Structure)
    outline = call_ai(topic, "Create 4 headings JSON: {'headings':['h1','h2','h3','h4']}")
    if not outline or 'headings' not in outline: 
        logger.error("❌ Échec de la structure (Headings)")
        return None

    # 2. BODY (Rédaction du corps)
    body = ""
    for h in outline["headings"]:
        txt = call_ai(h, f"Write a professional Hebrew paragraph about {h} for {BRAND_CONTEXT}", False)
        if txt: body += f"<h2>{h}</h2>\n<p>{txt}</p>\n\n"

    if len(body) < 300: 
        logger.error("❌ Contenu trop court")
        return None

    # 3. FAQ (Le moteur de Rich Results Google)
    faq = call_ai(topic, "Create 3 FAQ JSON: {'faqs':[{'q':'','a':''}]}")
    faq_html = "<h3>שאלות נפוצות</h3>\n"
    faq_list_for_schema = []
    if faq and "faqs" in faq:
        for f in faq["faqs"]:
            q, a = f.get('q', ''), f.get('a', '')
            if q and a: 
                faq_html += f"<p><strong>{q}</strong><br>{a}</p>\n"
                faq_list_for_schema.append({"q": q, "a": a})

    # 4. META & SLUG (Identité SEO)
    meta = call_ai(topic, "SEO meta JSON: {'title':'','intro':'','desc':''}")
    if not meta or not meta.get("title"): return None

    # Slug propre sans caractères hébreux
    slug_base = re.sub(r'[^a-z0-9-]', '-', keyword.lower()).strip('-')
    slug = f"{slug_base}-{uuid.uuid4().hex[:4]}"
    
    # Tracking ID pour l'Agent 20
    campaign_id = f"SEO_{uuid.uuid4().hex[:6]}"
    wa_link = f"https://kalride.co.il/go/{campaign_id}"
    
    # 5. SCHEMA (Le "cerveau" pour les robots Google)
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta.get("title", ""),
        "description": meta.get("desc", ""),
        "author": {"@type": "Organization", "name": "Kal Ride"},
        "mainEntity": [
            {
                "@type": "Question", 
                "name": f['q'], 
                "acceptedAnswer": {"@type": "Answer", "text": f['a']}
            } for f in faq_list_for_schema
        ]
    }

    # 6. ASSEMBLAGE FINAL (HTML)
    full_html = f"""
    <h1>{meta.get('title')}</h1>
    <p><strong>{meta.get('intro','')}</strong></p>
    {body}
    {faq_html}
    {get_internal_links()}
    <br><p>🚀 <strong>מוכנים לאדרנלין?</strong> <a href='{wa_link}'>לחצו כאן לשריון מקום בווצאפ!</a></p>
    <script type="application/ld+json">
    {json.dumps(schema, ensure_ascii=False)}
    </script>
    """

    return {
        "slug": slug, 
        "title": meta.get("title"), 
        "content": full_html, 
        "desc": meta.get("desc"), 
        "campaign_id": campaign_id, 
        "keyword": keyword
    }
# ==========================================
# 5. EXECUTION PIPELINE
# ==========================================
def run_v6_hybrid():
    logger.info("🚀 V6 HYBRID ENGINE STARTING")
    
    keywords = generate_keywords()
    angles = ["extreme", "romantic", "family", "nature"]

    for kw in keywords[:1]:  
        for angle in angles[:1]: 
            
            article = generate_article(kw, angle)
            if not article:
                logger.warning(f"⚠️ Failed to generate article for {kw}")
                continue

            try:
                supabase.table("articles").insert({
                    "slug": article["slug"],
                    "title_he": article["title"],
                    "content_he": article["content"],
                    "meta_description": article["desc"],
                    "status": "published",
                    "language_code": "he"
                }).execute()
                
                # שמירה לטבלת הלמידה כדי שסוכן 20 יתחיל לעבוד
                supabase.table("agent_learning").insert({
                    "campaign_id": article["campaign_id"],
                    "trend_concept": article["keyword"],
                    "status": "success",
                    "clicks": 0
                }).execute()

                logger.info(f"✅ DB SAVED: {kw} | Angle: {angle}")
            except Exception as e:
                logger.error(f"DB Error: {e}")

    logger.info("🏁 V6 HYBRID DONE")

if __name__ == "__main__":
    run_v6_hybrid()