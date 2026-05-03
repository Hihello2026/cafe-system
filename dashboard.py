import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
BRANCHES = {
    "شارع التلفزيون": (24.6475, 46.7042),
    "شارع الخزان": (24.6412, 46.7035)
}
DB_FILE = "orders.csv"

# ذاكرة السلة العالمية
if 'user_carts' not in globals():
    user_carts = {}

# --- 2. تحسين تصميم الواجهة (CSS) ---
st.set_page_config(page_title="CAFE ORDER SYSTEM", layout="wide", page_icon="☕")

# إضافة لمسة التصميم الصناعي البسيط
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #333; color: white; }
    .stTable { background-color: white; border-radius: 10px; }
    h1 { color: #1a1a1a; font-family: 'Inter', sans-serif; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

st.title("☕ CAFE ORDER SYSTEM")
st.caption("نظام إدارة الفروع والطلبات المسبقة - تايمن (TIMENN)")

# --- 3. إدارة البيانات ---
def load_orders():
    if os.path.isfile(DB_FILE):
        try: 
            df = pd.read_csv(DB_FILE)
            # ترتيب الأعمدة لشكل احترافي
            return df[['الوقت', 'العميل', 'الطلب', 'الفرع', 'المسافة']]
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 4. تخطيط الصفحة ---
col_stats, col_table = st.columns([1, 3])

with col_stats:
    st.subheader("📊 ملخص اليوم")
    df = load_orders()
    if not df.empty:
        st.metric("إجمالي الطلبات", len(df))
        st.metric("أكثر فرع طلباً", df['الفرع'].mode()[0] if not df.empty else "-")
    
    st.divider()
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

with col_table:
    st.subheader("📋 سجل العمليات الحية")
    if st.button("🔄 تحديث الطلبات"):
        st.rerun()
    
    if not df.empty:
        # عرض الجدول بشكل تنازلي (الأحدث فوق) مع تلوين الفروع
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("نظام الرادار يعمل.. بانتظار أول طلب.")

# --- 5. محرك البوت المطور ---
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
        await message.answer("مرحباً بك في **TIMENN**.\nيرجى اختيار الأصناف لإضافتها لسلتك:", reply_markup=markup)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def add_to_cart(message: types.Message):
        user_id = message.from_user.id
        item = message.text
        if user_id not in user_carts: user_carts[user_id] = {}
        user_carts[user_id][item] = user_carts[user_id].get(item, 0) + 1
        
        summary = "\n".join([f"• {k}: {v}" for k, v in user_carts[user_id].items()])
        kb = [[types.KeyboardButton(text="📍 إرسال الموقع وتأكيد الطلب", request_location=True)],
              [types.KeyboardButton(text="➕ إضافة صنف آخر")]]
        await message.answer(f"🛒 **السلة الحالية:**\n{summary}\n\nجاهز لإرسال الطلب؟", 
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        user_id = message.from_user.id
        if user_id in user_carts and user_carts[user_id]:
            order_text = ", ".join([f"{v}x {k}" for k, v in user_carts[user_id].items()])
            u_coords = (message.location.latitude, message.location.longitude)
            
            distances = {name: geodesic(u_coords, coords).km for name, coords in BRANCHES.items()}
            nearest = min(distances, key=distances.get)
            
            # حفظ الطلب
            new_entry = {
                "العميل": message.from_user.first_name,
                "الطلب": order_text,
                "الفرع": nearest,
                "المسافة": f"{distances[nearest]:.2f} كم",
                "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
            }
            pd.DataFrame([new_entry]).to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
            
            user_carts[user_id] = {} # تفريغ السلة
            await message.answer(f"✅ تم تأكيد طلبك لفرع **{nearest}**.\nنتطلع لرؤيتك قريباً!")
        else:
            await message.answer("السلة فارغة، يرجى اختيار طلب أولاً.")

    await dp.start_polling(bot, handle_signals=False)

if st.button("🚀 تشغيل نظام CAFE ORDER SYSTEM"):
    st.success("النظام نشط الآن")
    asyncio.run(start_bot())
