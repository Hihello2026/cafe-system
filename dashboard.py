import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) # إحداثيات موقعك في الرياض

st.set_page_config(page_title="TIMENN Live Tracking", layout="wide")
st.title("🏎️ لوحة تايمن - مراقبة وصول العملاء")

# تهيئة القائمة في الجلسة
if 'order_list' not in st.session_state:
    st.session_state.order_list = []

# --- واجهة العرض ---
st.subheader("حالة المسار الحالية")
table_placeholder = st.empty()

def update_display():
    if st.session_state.order_list:
        df = pd.DataFrame(st.session_state.order_list)
        table_placeholder.table(df)
    else:
        table_placeholder.info("بانتظار استقبال إشارات الموقع...")

# --- وظائف البوت المحسنة لـ Streamlit ---
async def run_bot_logic():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def welcome(message: types.Message):
        kb = [[types.KeyboardButton(text="📍 مشاركة الموقع للتحضير", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("مرحباً بك في تايمن! شارك موقعك لنعرف متى نجهز قهوتك:", reply_markup=markup)

    @dp.message(F.location)
    async def get_loc(message: types.Message):
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        status = "🚨 عند الشباك" if dist < 0.3 else "⏳ قادم في الطريق"
        
        new_data = {
            "العميل": message.from_user.first_name,
            "المسافة": f"{dist:.2f} كم",
            "الحالة": status,
            "التوقيت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        # تحديث القائمة
        st.session_state.order_list.insert(0, new_data)
        await message.answer(f"استلمنا إشارتك! أنت على بُعد {dist:.2f} كم.")

    # تشغيل البوت بدون استخدام set_wakeup_fd لتجنب خطأ الـ Thread
    await dp.start_polling(bot, handle_signals=False)

# --- زر التشغيل الآمن ---
if st.button("بدء استقبال إشارات الموقع 🛰️"):
    update_display()
    # استخدام loop مخصص لـ Streamlit
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_bot_logic())
    except Exception as e:
        st.error(f"تنبيه: {e}")

update_display()
