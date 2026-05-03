import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
# إحداثيات الرياض (حدثها لاحقاً لموقعك الفعلي)
CAFE_LOCATION = (24.7136, 46.6753)

st.set_page_config(page_title="TIMENN Dashboard", layout="wide")
st.title("🏎️ لوحة تايمن - إدارة الطلبات")

if 'final_orders' not in st.session_state:
    st.session_state.final_orders = []
if 'temp_selection' not in st.session_state:
    st.session_state.temp_selection = {}

# --- عرض الجدول في الموقع ---
st.subheader("سجل الطلبات الحية")
table_placeholder = st.empty()

def render_table():
    if st.session_state.final_orders:
        df = pd.DataFrame(st.session_state.final_orders)
        table_placeholder.table(df)
    else:
        table_placeholder.info("بانتظار استقبال الطلبات من تيليقرام...")

render_table()

# --- محرك البوت ---
async def main_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def open_menu(message: types.Message):
        # إنشاء أزرار المنيو
        buttons = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer("مرحباً بك في تايمن! اختر صنفك المفضل من المنيو أدناه:", reply_markup=keyboard)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def process_choice(message: types.Message):
        st.session_state.temp_selection[message.from_user.id] = message.text
        
        loc_btn = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        loc_keyboard = types.ReplyKeyboardMarkup(keyboard=loc_btn, resize_keyboard=True)
        await message.answer(f"تم اختيار {message.text}. فضلاً شاركنا موقعك لنحدد وقت الوصول:", reply_markup=loc_keyboard)

    @dp.message(F.location)
    async def process_location(message: types.Message):
        user_id = message.from_user.id
        selected_item = st.session_state.temp_selection.get(user_id, "طلب عام")
        
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        
        new_entry = {
            "العميل": message.from_user.first_name,
            "الطلب": selected_item,
            "المسافة": f"{dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        st.session_state.final_orders.insert(0, new_entry)
        await message.answer("رائع! طلبك الآن يظهر على شاشة التحضير في المقهى.")
        st.rerun()

    await dp.start_polling(bot, handle_signals=False)

if st.button("تفعيل استقبال الطلبات 🛰️"):
    asyncio.run(main_bot())
