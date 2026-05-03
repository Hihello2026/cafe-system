import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) 
DB_FILE = "orders.csv"

st.set_page_config(page_title="TIMENN Pit Stop", layout="wide")
st.title("🏎️ لوحة تايمن - المراقبة الحية")

# وظائف قاعدة البيانات
def save_order(entry):
    df = pd.DataFrame([entry])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_orders():
    if os.path.isfile(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

# --- واجهة العرض ---
st.subheader("سجل العمليات")
if st.button("تحديث الجدول 🔄"):
    st.rerun()

orders_df = load_orders()
if not orders_df.empty:
    st.table(orders_df.iloc[::-1])
else:
    st.info("بانتظار إشارات العملاء...")

if st.button("تصفير السجل 🗑️"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.rerun()

# --- محرك البوت ---
async def main_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        menu_kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=menu_kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer("مرحباً بك في تايمن! اختر صنفك المفضل:", reply_markup=keyboard)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def process_choice(message: types.Message):
        if 'temp_selection' not in st.session_state:
            st.session_state.temp_selection = {}
        st.session_state.temp_selection[message.from_user.id] = message.text
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer(f"تم اختيار {message.text}. شاركنا موقعك الآن:", reply_markup=markup)

    @dp.message(F.location)
    async def process_location(message: types.Message):
        uid = message.from_user.id
        item = st.session_state.get('temp_selection', {}).get(uid, "طلب متنوع")
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        new_entry = {
            "العميل": message.from_user.first_name,
            "الطلب": item,
            "المسافة": f"{dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(new_entry)
        await message.answer("تم! طلبك يظهر الآن في اللوحة.")
        st.rerun()

    await dp.start_polling(bot, handle_signals=False)

if st.button("تفعيل الرادار 🛰️"):
    asyncio.run(main_bot())
