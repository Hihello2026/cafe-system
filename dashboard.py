import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات الأساسية ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) # موقع الرياض الحالي

st.set_page_config(page_title="TIMENN Dashboard", layout="wide")
st.title("🏎️ لوحة تايمن - إدارة الطلبات الحية")

# تهيئة المخزن المؤقت للبيانات
if 'final_orders' not in st.session_state:
    st.session_state.final_orders = []
if 'temp_selection' not in st.session_state:
    st.session_state.temp_selection = {}

# --- عرض الجدول ---
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
        # مصفوفة الأزرار
        menu_kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        # resize_keyboard تجعل الأزرار بحجم مناسب
        # one_time_keyboard تختفي بعد الضغط
        keyboard = types.ReplyKeyboardMarkup(keyboard=menu_kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer("مرحباً بك في تايمن! اختر صنفك المفضل:", reply_markup=keyboard)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def process_choice(message: types.Message):
        # حفظ الاختيار باستخدام ID المستخدم
        st.session_state.temp_selection[message.from_user.id] = message.text
        
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        loc_markup = types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer(f"اختيار رائع: {message.text}\nفضلاً شاركنا موقعك الآن:", reply_markup=loc_markup)

    @dp.message(F.location)
    async def process_location(message: types.Message):
        uid = message.from_user.id
        selected_item = st.session_state.temp_selection.get(uid, "طلب متنوع")
        
        # حساب المسافة
        u_coords = (message.location.latitude, message.location.longitude)
        dist = geodesic(u_coords, CAFE_LOCATION).km
        
        # إضافة الطلب للقائمة
        new_entry = {
            "العميل": message.from_user.first_name,
            "الطلب": selected_item,
            "المسافة": f"{dist:.2f} كم",
            "التوقيت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        st.session_state.final_orders.insert(0, new_entry)
        await message.answer("تم استلام طلبك! سيظهر الآن في لوحة التحكم بالمقهى.")
        # تحديث الواجهة فوراً
        st.rerun()

    await dp.start_polling(bot, handle_signals=False)

# --- زر التشغيل ---
if st.button("تفعيل رادار تايمن 🛰️"):
    try:
        asyncio.run(main_bot())
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
