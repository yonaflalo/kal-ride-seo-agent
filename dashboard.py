import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
import plotly.express as px # ספרייה מעולה לגרפים אינטראקטיביים

# ==========================================
# 1. חיבור וקונפיגורציה
# ==========================================
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="Kal Ride AI Command Center", layout="wide", page_icon="📊")

# --- שפות ו-RTL ---
lang = st.sidebar.radio("Select Language / בחר שפה", ["עברית", "English"])
is_hebrew = lang == "עברית"

if is_hebrew:
    st.markdown("""<style>body { direction: rtl; text-align: right; }</style>""", unsafe_allow_html=True)
    t = {
        "title": "📊 לוח בקרה אסטרטגי - Kal Ride AI",
        "sidebar": "ניהול מערכת",
        "menu": ["לוח בקרה", "ניתוח אסטרטגי", "ארכיון תוכן", "הגדרות"],
        "kpi_total": "סך סבבים",
        "kpi_wait": "עצירות (מניעת ספאם)",
        "kpi_success": "פרסומים מוצלחים",
        "chart_actions": "התפלגות החלטות ה-CMO",
        "chart_trends": "טרנדים מובילים",
        "latest_logic": "הלוגיקה מאחורי ההחלטה האחרונה",
        "no_data": "ממתין לנתונים מהסוכן..."
    }
else:
    t = {
        "title": "📊 Kal Ride AI Strategic Dashboard",
        "sidebar": "System Management",
        "menu": ["Dashboard", "Strategic Analysis", "Content Archive", "Settings"],
        "kpi_total": "Total Cycles",
        "kpi_wait": "Wait (Spam Prevention)",
        "kpi_success": "Successful Posts",
        "chart_actions": "CMO Decision Distribution",
        "chart_trends": "Top Trending Concepts",
        "latest_logic": "Latest Decision Logic",
        "no_data": "Waiting for Agent data..."
    }

st.sidebar.title(t["sidebar"])
choice = st.sidebar.selectbox("Menu / תפריט", t["menu"])

# ==========================================
# 2. עיבוד דאטה (BI Logic)
# ==========================================
@st.cache_data(ttl=60) # רענון כל דקה
def load_ai_data():
    res = supabase.table("agent_learning").select("*").order("created_at", desc=True).execute()
    data = pd.DataFrame(res.data)
    if not data.empty:
        # חילוץ סוג הפעולה מתוך המחרוזת action_taken
        data['action_type'] = data['action_taken'].str.extract(r'Action: (\w+)')[0]
        data['created_at'] = pd.to_datetime(data['created_at'])
    return data

df = load_ai_data()

# ==========================================
# 3. תצוגת תוכן
# ==========================================
st.title(t["title"])

if df.empty:
    st.info(t["no_data"])
else:
    if choice in ["לוח בקרה", "Dashboard"]:
        # --- שורת KPI ---
        c1, c2, c3 = st.columns(3)
        total_runs = len(df)
        wait_count = len(df[df['action_type'] == 'WAIT'])
        success_posts = len(df[df['action_taken'].str.contains("Published|POST", na=False)])
        
        c1.metric(t["kpi_total"], total_runs)
        c2.metric(t["kpi_wait"], wait_count, delta=f"{(wait_count/total_runs)*100:.0f}%", delta_color="normal")
        c3.metric(t["kpi_success"], success_posts)

        st.divider()

        # --- גרפים ותובנות ---
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader(t["chart_actions"])
            fig_pie = px.pie(df, names='action_type', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_b:
            st.subheader(t["latest_logic"])
            latest = df.iloc[0]
            st.success(f"**Trend:** {latest['trend_concept']}")
            st.info(f"**AI Reason:** {latest['insight']}")

        st.divider()
        
        # גרף ציר זמן - פעילות המכונה
        st.subheader("Activity Timeline / ציר זמן פעילות")
        df_timeline = df.set_index('created_at').resample('D').count()
        st.area_chart(df_timeline['trend_concept'])

    elif choice in ["ניתוח אסטרטגי", "Strategic Analysis"]:
        st.subheader(t["chart_trends"])
        # ניתוח מילים נפוצות בטרנדים
        trend_counts = df['trend_concept'].value_counts().head(10)
        st.bar_chart(trend_counts)
        
        st.write("---")
        st.subheader("Deep Archive / ארכיון תובנות")
        for idx, row in df.iterrows():
            with st.expander(f"{row['created_at'].strftime('%d/%m %H:%M')} - {row['trend_concept']}"):
                st.write(f"**Action:** {row['action_taken']}")
                st.write(f"**Logic:** {row['insight']}")

# כפתור רענון
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()