import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. الإعدادات الأساسية ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) # موقع الرياض الحالي
DB_FILE = "orders.csv"

st.set_page_config(page_title="TIMENN Dashboard", layout="wide", page_icon="🏎️")
st.title("🏎️ لوحة تايمن - المراقبة الحية للطلبات")

# --- 2. وظائف إدارة البيانات ---
def save_order(entry):
    """حفظ الطلب في ملف CSV لضمان استمرارية البيانات"""
    df = pd.DataFrame([entry])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_orders():
    """قراءة الطلبات من الملف"""
    if os.path.isfile(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 3. واجهة المستخدم في Streamlit ---
col_table, col_ctrl = st.columns([3, 1])

with col_table:
    st.subheader("سجل الطلبات الحية")
    if st.button("🔄 تحديث الجدول"):
        st.rerun()
    
    orders_df = load_orders()
    if not orders_df.empty:
        # ترتيب الطلبات ليكون الأحدث في الأعلى
        st.table(orders_df.iloc[::-1])
    else:
        st.info("الرادار يبحث عن إشارات.. استقبل الطلبات في تيليقرام ثم اضغط تحديث.")

with col_ctrl:
    st.subheader("الإدارة")
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        st.success("تم مسح السجل")
        st.rerun()

# --- 4. محرك البوت ---
async def start_bot():
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
        await message.answer("أهلاً بك في تايمن! اختر صنفك المفضل:", reply_markup=keyboard)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def process_choice(message: types.Message):
        # حفظ الاختيار مؤقتاً
        st.session_state['last_item'] = message.text
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer(f"تم اختيار {message.text}. فضلاً شاركنا موقعك الآن للتحضير:", reply_markup=markup)

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        item = st.session_state.get('last_item', "طلب متنوع")
        user_coords = (message.location.latitude, message.location.longitude)
        distance = geodesic(user_coords, CAFE_LOCATION).km
        
        new_entry = {
            "العميل": message.from_user.first_name,
            "الطلب": item,
            "المسافة": f"{distance:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        save_order(new_entry)
        await message.answer("✅ رائع! طلبك الآن يظهر على شاشة المقهى.")

    # تعطيل معالجة الإشارات لمنع الـ RuntimeError في Streamlit Cloud
    await dp.start_polling(bot, handle_signals=False)

# --- 5. التشغيل ---
if st.button("🛰️ تفعيل رادار تايمن"):
    st.warning("الرادار يعمل الآن.. استقبل الطلبات في تيليقرام ثم اضغط 'تحديث الجدول' هنا.")
    try:
        asyncio.run(start_bot())
    except Exception as e:
        st.error(f"تنبيه: {e}")
