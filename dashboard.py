import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات الأساسية ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) # موقع افتراضي (يمكنك تعديله لاحقاً)

# --- واجهة Streamlit ---
st.set_page_config(page_title="TIMENN Cafe Dashboard", layout="wide")
st.title("🏎️ لوحة تحكم الدرايف ثرو - تايمن")

if 'orders' not in st.session_state:
    st.session_state.orders = []

# عرض الجدول
st.subheader("مراقبة الطلبات الحية ومواقع العملاء")
if st.session_state.orders:
    df = pd.DataFrame(st.session_state.orders)
    st.table(df)
else:
    st.info("بانتظار أول طلب من البوت...")

# --- منطق البوت (الذي يعمل في الخلفية) ---
async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        kb = [
            [types.KeyboardButton(text="☕️ لاتيه", callback_data="latte")],
            [types.KeyboardButton(text="🥐 كروسان", callback_data="croissant")],
            [types.KeyboardButton(text="📍 مشاركة الموقع للتحضير", request_location=True)]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("أهلاً بك في مقهى تايمن! اختر طلبك وشاركنا موقعك لنحضره فور وصولك:", reply_markup=keyboard)

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        user_coords = (message.location.latitude, message.location.longitude)
        dist = geodesic(user_coords, CAFE_LOCATION).km
        
        status = "وصل الآن! 🚨" if dist < 0.5 else "في الطريق (قادم) ⏳"
        
        # إضافة الطلب للقائمة في اللوحة
        new_order = {
            "العميل": message.from_user.first_name,
            "المسافة": f"{dist:.2f} كم",
            "الحالة": status
        }
        st.session_state.orders.append(new_order)
        await message.answer(f"تم استلام موقعك! أنت على بُعد {dist:.2f} كم. قهوتك بانتظارك!")

    # ملاحظة: Streamlit لا يسمح بتشغيل البوت بشكل دائم بسهولة، 
    # لذا سنستخدم هذا الزر فقط للتجربة الآن
    if st.button("تفعيل استقبال الطلبات"):
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except:
        pass
