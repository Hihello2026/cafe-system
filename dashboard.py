import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) 

st.set_page_config(page_title="TIMENN Pit Stop", layout="wide")
st.title("🏎️ لوحة تايمن - مراقبة المسار")

# استخدام st.cache_resource لتخزين البيانات خارج نطاق إعادة تحميل الصفحة
if 'shared_orders' not in st.session_state:
    st.session_state.shared_orders = []

st.subheader("الطلبات الحية")
table_spot = st.empty()

# وظيفة لعرض البيانات
def refresh_ui():
    if st.session_state.shared_orders:
        df = pd.DataFrame(st.session_state.shared_orders)
        table_spot.table(df)
    else:
        table_spot.info("بانتظار الإشارة القادمة...")

# --- محرك البوت ---
async def start_listening():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(F.location)
    async def handle_loc(message: types.Message):
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        status = "🚨 وصول!" if dist < 0.5 else "⏳ قادم"
        
        entry = {
            "العميل": message.from_user.first_name,
            "المسافة": f"{dist:.2f} كم",
            "الحالة": status,
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        # التحديث في قائمة الجلسة
        st.session_state.shared_orders.insert(0, entry)
        await message.answer(f"وصلت إشارتك لبرج المراقبة! تبعد {dist:.2f} كم.")
        # نطلب من واجهة Streamlit إعادة التحميل
        st.rerun()

    await dp.start_polling(bot, handle_signals=False)

# زر التشغيل
if st.button("تفعيل الرادار 🛰️"):
    asyncio.run(start_listening())

refresh_ui()
