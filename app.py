import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date
import plotly.express as px

# ==========================================
# 1. إعدادات الواجهة (Terminal Theme)
# ==========================================
st.set_page_config(page_title="DevOps Scholar", page_icon="💻", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #39ff14; font-family: 'Courier New', Courier, monospace; }
    h1, h2, h3 { color: #39ff14 !important; }
    .stSelectbox label, .stDateInput label { color: #39ff14; }
    hr { border-color: #39ff14; opacity: 0.3; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. الاتصال بقاعدة البيانات
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

# إحضار المواد من الداتا بيز
def get_subjects():
    try:
        res = supabase.table('current_subjects').select('subject_name').eq('is_active', True).execute()
        return [r['subject_name'] for r in res.data]
    except:
        return ["English", "Python", "Linux", "Bash", "MCSA"]

subjects = get_subjects()

# ==========================================
# 3. واجهة التطبيق
# ==========================================
st.title("💻 DevOps Scholar | Deep Work System")

tab1, tab2 = st.tabs(["📝 تسجيل الساعات (Log)", "📊 لوحة التحكم (Analytics)"])

with tab1:
    st.subheader("📅 خطة اليوم وتوزيع الساعات")
    selected_date = st.date_input("اختر اليوم", date.today())
    st.markdown("---")
    
    time_slots = [
        "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM", "10:00 AM - 11:00 AM",
        "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM", "01:00 PM - 02:00 PM", "02:00 PM - 03:00 PM",
        "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM",
        "07:00 PM - 08:00 PM", "08:00 PM - 09:00 PM", "09:00 PM - 10:00 PM", "10:00 PM - 11:00 PM",
        "11:00 PM - 12:00 AM"
    ]

    log_data = []
    
    c1, c2, c3 = st.columns([1, 1, 1])
    c1.markdown("**الساعة**")
    c2.markdown("**نوع العمل**")
    c3.markdown("**المادة**")

    for slot in time_slots:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.markdown(f"<div style='padding-top: 10px;'>{slot}</div>", unsafe_allow_html=True)
        with c2:
            b_type = st.selectbox(f"Type ({slot})", ["لم يتم الاستغلال", "Deep Work (تركيز 100%)", "Shallow Work (مذاكرة خفيفة)", "Break (راحة)"], label_visibility="collapsed", key=f"type_{slot}")
        with c3:
            subj = st.selectbox(f"Subject ({slot})", ["لا يوجد"] + subjects, label_visibility="collapsed", key=f"subj_{slot}")
        
        if b_type != "لم يتم الاستغلال" and b_type != "Break (راحة)":
            log_data.append({
                "log_date": str(selected_date),
                "time_slot": slot,
                "block_type": b_type,
                "subject": subj if subj != "لا يوجد" else "عام"
            })

    st.markdown("---")
    if st.button("🚀 تشفير وحفظ السجل اليومي", use_container_width=True):
        with st.spinner("جاري التخزين السحابي..."):
            supabase.table('time_blocks').delete().eq('log_date', str(selected_date)).execute()
            if log_data:
                supabase.table('time_blocks').insert(log_data).execute()
            st.success("✅ تم حفظ إنجازك بنجاح! راجع لوحة التحكم.")

with tab2:
    st.subheader("📈 مقاييس الأداء (Level & XP)")
    try:
        res = supabase.table('time_blocks').select('*').execute()
        if res.data:
            df = pd.DataFrame(res.data)
            
            # حساب النقاط: DeepWork = 30 نقطة، Shallow = 10 نقاط
            deep_hours = len(df[df['block_type'] == 'Deep Work (تركيز 100%)'])
            shallow_hours = len(df[df['block_type'] == 'Shallow Work (مذاكرة خفيفة)'])
            total_xp = (deep_hours * 30) + (shallow_hours * 10)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔥 إجمالي النقاط (XP)", f"{total_xp}")
            col2.metric("🧠 ساعات العمل العميق", deep_hours)
            col3.metric("📖 ساعات العمل السطحي", shallow_hours)

            st.markdown("---")
            st.markdown("### 📚 التوزيع الزمني للمواد (Heatmap)")
            
            # رسم بياني احترافي لتوزيع المواد
            subj_counts = df[df['subject'] != '']['subject'].value_counts().reset_index()
            subj_counts.columns = ['المادة', 'عدد الساعات']
            fig = px.pie(subj_counts, values='عدد الساعات', names='المادة', hole=0.4, 
                         color_discrete_sequence=['#39ff14', '#2e8b57', '#00ff7f', '#228b22', '#32cd32'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("لا توجد بيانات مسجلة بعد. اذهب وسجل أولى ساعاتك!")
    except Exception as e:
        st.error("جاري تجهيز لوحة التحكم...")
