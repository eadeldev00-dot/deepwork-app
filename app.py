import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date
import plotly.express as px

# ==========================================
# 1. إعدادات الواجهة وتجربة المستخدم (UI/UX)
# ==========================================
st.set_page_config(page_title="DevOps Scholar", page_icon="💻", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #39ff14; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #39ff14 !important; }
    .stSelectbox label, .stDateInput label, .stTextInput label { color: #39ff14 !important; font-weight: bold; }
    hr { border-color: #39ff14; opacity: 0.2; }
    .css-1d391kg, .css-1lcbmhc { background-color: #161b22; border-right: 1px solid #39ff14; } /* Sidebar Styling */
    .stButton>button { background-color: #238636; color: white; border-radius: 5px; border: 1px solid #2ea043; transition: 0.3s; }
    .stButton>button:hover { background-color: #2ea043; border-color: #39ff14; }
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
    st.error(f"خطأ في الاتصال بالسحابة: {e}")
    st.stop()

# ==========================================
# 3. دوال جلب وإضافة البيانات
# ==========================================
def get_subjects():
    try:
        res = supabase.table('current_subjects').select('subject_name').eq('is_active', True).execute()
        return [r['subject_name'] for r in res.data]
    except:
        return []

subjects = get_subjects()

# ==========================================
# 4. القائمة الجانبية (Sidebar) - تحسين الـ UX
# ==========================================
with st.sidebar:
    st.header("⚙️ إعدادات اليوم")
    selected_date = st.date_input("📅 اختر اليوم:", date.today())
    
    st.markdown("---")
    st.header("📚 إدارة المواد")
    new_subject = st.text_input("أدخل اسم مادة جديدة:")
    if st.button("➕ إضافة المادة", use_container_width=True):
        if new_subject:
            if new_subject not in subjects:
                try:
                    supabase.table('current_subjects').insert({'subject_name': new_subject}).execute()
                    st.success(f"تمت إضافة '{new_subject}' بنجاح!")
                    st.rerun() # تحديث الصفحة فوراً لتظهر المادة في القوائم
                except Exception as e:
                    st.error("حدث خطأ أثناء الإضافة.")
            else:
                st.warning("المادة موجودة بالفعل!")
        else:
            st.warning("يرجى كتابة اسم المادة أولاً.")
            
    st.markdown("---")
    st.info("💡 **نصيحة:** ساعات العمل العميق (Deep Work) تمنحك 3 أضعاف نقاط الخبرة (XP) مقارنة بالعمل السطحي.")

# ==========================================
# 5. الواجهة الرئيسية للمستخدم (Main UI)
# ==========================================
st.title("💻 DevOps Scholar | Terminal")

tab1, tab2 = st.tabs(["📝 سجل الساعات (Log)", "📊 لوحة التحكم (Analytics)"])

with tab1:
    st.subheader(f"توزيع فترات يوم: {selected_date}")
    
    time_slots = [
        "07:00 AM - 08:00 AM", "08:00 AM - 09:00 AM", "09:00 AM - 10:00 AM", "10:00 AM - 11:00 AM",
        "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM", "01:00 PM - 02:00 PM", "02:00 PM - 03:00 PM",
        "03:00 PM - 04:00 PM", "04:00 PM - 05:00 PM", "05:00 PM - 06:00 PM", "06:00 PM - 07:00 PM",
        "07:00 PM - 08:00 PM", "08:00 PM - 09:00 PM", "09:00 PM - 10:00 PM", "10:00 PM - 11:00 PM",
        "11:00 PM - 12:00 AM"
    ]

    log_data = []
    
    # عناوين الأعمدة بشكل أنظف
    c1, c2, c3 = st.columns([1, 1.5, 1.5])
    c1.markdown("### ⏰ الفترة الزمنية")
    c2.markdown("### 🎯 نوع التركيز")
    c3.markdown("### 📖 المادة")
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

    for slot in time_slots:
        c1, c2, c3 = st.columns([1, 1.5, 1.5])
        with c1:
            st.markdown(f"<div style='font-size: 16px; font-weight: bold; padding-top: 8px;'>{slot}</div>", unsafe_allow_html=True)
        with c2:
            b_type = st.selectbox(f"Type {slot}", ["لم يتم الاستغلال", "Deep Work (تركيز 100%)", "Shallow Work (مذاكرة خفيفة)", "Break (راحة)"], label_visibility="collapsed", key=f"type_{slot}")
        with c3:
            subj = st.selectbox(f"Subject {slot}", ["لا يوجد"] + subjects, label_visibility="collapsed", key=f"subj_{slot}")
        
        if b_type != "لم يتم الاستغلال" and b_type != "Break (راحة)":
            log_data.append({
                "log_date": str(selected_date),
                "time_slot": slot,
                "block_type": b_type,
                "subject": subj if subj != "لا يوجد" else "عام"
            })

    st.markdown("---")
    if st.button("🚀 تشفير وحفظ السجل اليومي بالسحابة", use_container_width=True):
        with st.spinner("جاري تأمين بياناتك في Supabase..."):
            supabase.table('time_blocks').delete().eq('log_date', str(selected_date)).execute()
            if log_data:
                supabase.table('time_blocks').insert(log_data).execute()
            st.success("✅ تم حفظ المهام بنجاح! راجع لوحة التحكم لترى تقدمك.")

with tab2:
    st.subheader("📈 إحصائياتك الشاملة وتطور المستوى")
    try:
        res = supabase.table('time_blocks').select('*').execute()
        if res.data:
            df = pd.DataFrame(res.data)
            
            deep_hours = len(df[df['block_type'] == 'Deep Work (تركيز 100%)'])
            shallow_hours = len(df[df['block_type'] == 'Shallow Work (مذاكرة خفيفة)'])
            total_xp = (deep_hours * 30) + (shallow_hours * 10)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🔥 نقاط الخبرة (XP)", f"{total_xp} نقطة")
            col2.metric("🧠 ساعات العمل العميق", f"{deep_hours} ساعة")
            col3.metric("📖 ساعات العمل السطحي", f"{shallow_hours} ساعة")

            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 📚 توزيع الساعات على المواد")
                subj_counts = df[df['subject'] != '']['subject'].value_counts().reset_index()
                subj_counts.columns = ['المادة', 'عدد الساعات']
                fig_pie = px.pie(subj_counts, values='عدد الساعات', names='المادة', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Greens_r)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.markdown("### 📊 كثافة التركيز")
                type_counts = df['block_type'].value_counts().reset_index()
                type_counts.columns = ['النوع', 'العدد']
                fig_bar = px.bar(type_counts, x='النوع', y='العدد', color='النوع',
                                 color_discrete_map={'Deep Work (تركيز 100%)': '#39ff14', 'Shallow Work (مذاكرة خفيفة)': '#2e8b57'})
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#ffffff'))
                st.plotly_chart(fig_bar, use_container_width=True)

        else:
            st.info("لا توجد بيانات مسجلة بعد. ابدأ رحلتك الآن!")
    except Exception as e:
        st.error("جاري تجهيز البيانات...")
