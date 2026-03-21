import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("🔍 בודק איזה מודלים זמינים עבור המפתח שלך...")
try:
    for model in client.models.list():
        print(f"✅ מודל זמין: {model.name}")
except Exception as e:
    print(f"❌ שגיאה בשליפת מודלים: {e}")