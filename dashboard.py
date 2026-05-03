import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic
from streamlit_autorefresh import st_autorefresh

# --- 1. الإعدادات الأساسية ---
# توكن البوت الخاص بك
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'

# إحداثيات الفروع (الرياض)
BRANCHES = {
    "شارع التلفزيون": (24.6475, 46.7042),
    "شارع الخزان": (24.6412, 46.7035)
}
DB_FILE = "orders.csv"

# ذاكرة السلة المؤقتة للعملاء
if 'user_carts' not in globals():
    user_carts = {}

# --- 2. وظائف النظام المساعدة ---

def play_notification():
    """تشغيل صوت تنبيه عند وصول طلب جديد"""
    audio_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def load_orders_with_alert():
    """تحميل البيانات وتفعيل التنبيه الصوتي"""
    if os.path.isfile(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # التحقق من وجود طلبات جديدة لتشغيل الصوت
            if "last_count" not in st.session_state:
                st.session_state.last_count = len(df)
            elif len(df) > st.session_state.last_count:
                play_notification()
                st.session_state.last_count = len(df)
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 3. واجهة المستخدم (Modern Industrial Minimalism) ---
st.set_page_config(page_title="CAFE ORDER SYSTEM", layout="wide", page_icon="☕")

# تحديث تلقائي للواجهة كل 10 ثوانٍ لمراقبة الطلبات الحية
st_autorefresh(interval=10000, key="datarefresh")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    h1 { font-family: 'Inter', sans-serif; color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

st.title("☕ CAFE ORDER SYSTEM")
st.caption("نظام إدارة الفروع والطلبات المسبقة - تايمن (TIMENN) | Never Normal")

# تقسيم الشاشة: إحصائيات على اليسار وجدول على اليمين
col_stats, col_table = st.columns([1, 3])

with col_stats:
    st.subheader("📊 ملخص اليوم")
    df = load_orders_with_alert()
    if not df.empty:
        st.metric("إجمالي الطلبات", len(df))
        st.metric("الفرع الأكثر نشاطاً", df['الفرع'].mode()[0])
    
    st.divider()
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            st.session_state.last_count = 0
            st.rerun()

with col_table:
    st.subheader("📋 سجل العمليات الحية (تحديث تلقائي)")
    if not df.empty:
        # عرض أحدث الطلبات في الأعلى
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("بانتظار وصول طلبات جديدة من العملاء...")

# --- 4. محرك بوت التيليقرام (Logic) ---

async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه"), types.KeyboardButton(text="🧁 كيك مادلين")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع"), types.KeyboardButton(text="🥐 كروسان")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("مرحباً بك في **TIMENN**.\nاختر الأصناف التي ترغب بطلبها:", reply_markup=markup)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def add_to_cart(message: types.Message):
        user_id = message.from_user.id
        item = message.text
        if user_id not in user_carts:
            user_carts[user_id] = {}
        
        # زيادة الكمية في السلة
        user_carts[user_id][item] = user_carts[user_id].get(item, 0) + 1
        
        # عرض ملخص السلة للعميل
        summary = "\n".join([f"• {k}: {v}" for k, v in user_carts[user_id].items()])
        kb = [
            [types.KeyboardButton(text="📍 تأكيد الطلب وإرسال الموقع", request_location=True)],
            [types.KeyboardButton(text="➕ إضافة صنف آخر")]
        ]
        await message.answer(f"🛒 **سلتك الحالية:**\n{summary}\n\nهل تريد إضافة المزيد أم إرسال الموقع للتجهيز؟", 
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        user_id = message.from_user.id
        if user_id in user_carts and user_carts[user_id]:
            # تحويل السلة إلى نص واحد مدمج
            order_details = ", ".join([f"{v}x {k}" for k, v in user_carts[user_id].items()])
            u_coords = (message.location.latitude, message.location.longitude)
            
            # حساب المسافة لأقرب فرع
            distances = {name: geodesic(u_coords, coords).km for name, coords in BRANCHES.items()}
            nearest = min(distances, key=distances.get)
            
            # حفظ الطلب في الملف
            new_entry = {
                "الوقت": pd.Timestamp.now().strftime('%H:%M:%S'),
                "العميل": message.from_user.first_name,
                "الطلب": order_details,
                "الفرع": nearest,
                "المسافة": f"{distances[nearest]:.2f} كم"
            }
            pd.DataFrame([new_entry]).to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
            
            # تصفير سلة العميل بعد النجاح
            user_carts[user_id] = {}
            await message.answer(f"✅ تم استلام طلبك المجمع لفرع **{nearest}**.\nسيتم البدء في التجهيز فوراً، ننتظرك!")
        else:
            await message.answer("السلة فارغة! يرجى اختيار صنف من المنيو أولاً.")

    await dp.start_polling(bot, handle_signals=False)

# --- 5. تشغيل النظام ---
if st.button("🚀 تشغيل نظام CAFE ORDER SYSTEM الحيي"):
    st.success("الرادار والتنبيه الصوتي مفعل الآن.. بانتظار الطلبات.")
    asyncio.run(start_bot())
