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

st.set_page_config(page_title="TIMENN Dashboard", layout="wide")
st.title("🏎️ لوحة تايمن - المراقبة الحية")

# وظيفة الحفظ لضمان الكتابة الحقيقية على القرص
def save_order(entry):
    df = pd.DataFrame([entry])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_orders():
    if os.path.isfile(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- واجهة المستخدم ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("سجل العمليات")
    if st.button("🔄 تحديث يدوي للجدول"):
        st.rerun()
    
    orders_df = load_orders()
    if not orders_df.empty:
        st.table(orders_df.iloc[::-1]) # الأحدث فوق
    else:
        st.info("الرادار يبحث عن إشارات.. (اضغط تحديث بعد إرسال الموقع)")

with col2:
    st.subheader("التحكم")
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.rerun()

# --- محرك البوت ---
async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def welcome(message: types.Message):
        kb = [[types.KeyboardButton(text="☕️ قهوة لاتيه")], [types.KeyboardButton(text="🍃 شاي بالنعناع")]]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("أهلاً بك في تايمن! اختر طلبك:", reply_markup=markup)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع"]))
    async def ask_loc(message: types.Message):
        st.session_state['last_item'] = message.text
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع", request_location=True)]]
        await message.answer(f"تم اختيار {message.text}. أرسل موقعك الآن:", 
                             reply_markup=types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True))

    @dp.message(F.location)
    async def handle_loc(message: types.Message):
        item = st.session_state.get('last_item', "طلب")
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        
        entry = {
            "العميل": message.from_user.first_name,
            "الطلب": item,
            "المسافة": f"{dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(entry)
        await message.answer("✅ تم استلام طلبك بنجاح!")

    await dp.start_polling(bot)

if st.button("🛰️ تشغيل الرادار (اضغط مرة واحدة)"):
    st.warning("الرادار يعمل الآن.. استقبل الطلبات في تيليقرام ثم اضغط 'تحديث' هنا.")
    asyncio.run(start_bot())
