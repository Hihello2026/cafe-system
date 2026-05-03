import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
# إحداثيات الرياض التقريبية (تأكد من وضع إحداثيات مقهاك بدقة هنا)
CAFE_LOCATION = (24.7136, 46.6753) 

st.set_page_config(page_title="TIMENN Dashboard", layout="wide")
st.title("🏎️ لوحة تحكم تايمن - المراقبة الحية")

# تهيئة مخزن البيانات في الجلسة
if 'orders' not in st.session_state:
    st.session_state.orders = []

# عرض الجدول بشكل دائم
st.subheader("الطلبات القادمة")
placeholder = st.empty() # مكان مخصص لتحديث الجدول

def display_data():
    if st.session_state.orders:
        df = pd.DataFrame(st.session_state.orders)
        placeholder.table(df)
    else:
        placeholder.info("بانتظار وصول بيانات الموقع من العملاء...")

display_data()

# --- محرك البوت ---
async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        kb = [[types.KeyboardButton(text="📍 مشاركة الموقع للتحضير", request_location=True)]]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("مرحباً بك! اضغط الزر لمشاركة موقعك مع المقهى:", reply_markup=keyboard)

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        u_lat, u_lon = message.location.latitude, message.location.longitude
        dist = geodesic((u_lat, u_lon), CAFE_LOCATION).km
        
        # تحديد الحالة بناءً على المسافة
        status = "🚨 وصل الآن" if dist < 0.5 else "⏳ في الطريق"
        
        new_entry = {
            "العميل": message.from_user.first_name,
            "المسافة": f"{dist:.2f} كم",
            "الحالة": status,
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        st.session_state.orders.insert(0, new_entry) # إضافة الطلب الجديد في الأعلى
        st.success(f"تم استقبال موقع {message.from_user.first_name}!")
        st.rerun() # إجبار الصفحة على التحديث فوراً

    if st.button("تشغيل استقبال الإشارات 🛰️"):
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
