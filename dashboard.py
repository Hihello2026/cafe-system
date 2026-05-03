import streamlit as st
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
# إحداثيات الرياض التقريبية (حدثها لاحقاً لموقعك الفعلي)
CAFE_LOCATION = (24.7136, 46.6753)

st.set_page_config(page_title="TIMENN Order Dashboard", layout="wide")
st.title("🏎️ لوحة تايمن - إدارة الطلبات الحية")

# تهيئة مخزن البيانات في الجلسة
if 'order_data' not in st.session_state:
    st.session_state.order_data = {}
if 'final_orders' not in st.session_state:
    st.session_state.final_orders = []

st.subheader("قائمة الطلبات القادمة")
table_area = st.empty()

def update_table():
    if st.session_state.final_orders:
        df = pd.DataFrame(st.session_state.final_orders)
        table_area.table(df)
    else:
        table_area.info("بانتظار استقبال أول طلب...")

# --- محرك البوت ---
async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        # مصفوفة الأزرار للأصناف الأربعة
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
        await message.answer("أهلاً بك في تايمن! اختر صنفك المفضل أولاً:", reply_markup=keyboard)

    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def handle_choice(message: types.Message):
        # تخزين الصنف المختار مؤقتاً لكل مستخدم
        st.session_state.order_data[message.from_user.id] = message.text
        
        kb_loc = [[types.KeyboardButton(text="📍 مشاركة الموقع لتجهيز الطلب", request_location=True)]]
        markup_loc = types.ReplyKeyboardMarkup(keyboard=kb_loc, resize_keyboard=True)
        await message.answer(f"اختيار رائع ({message.text})! الآن شاركنا موقعك لنعرف متى نجهز طلبك:", reply_markup=markup_loc)

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        user_id = message.from_user.id
        # جلب الصنف الذي اختاره المستخدم سابقاً
        item = st.session_state.order_data.get(user_id, "طلب غير محدد")
        
        dist = geodesic((message.location.latitude, message.location.longitude), CAFE_LOCATION).km
        status = "🚨 استعد - وصول!" if dist < 0.5 else "⏳ قادم"
        
        order_entry = {
            "العميل": message.from_user.first_name,
            "الطلب": item,
            "المسافة": f"{dist:.2f} كم",
            "الحالة": status,
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        
        st.session_state.final_orders.insert(0, order_entry)
        await message.answer(f"تم! طلبك ({item}) مسجل، وأنت على بُعد {dist:.2f} كم.")
        st.rerun()

    await dp.start_polling(bot, handle_signals=False)

if st.button("تشغيل رادار تايمن 🛰️"):
    asyncio.run(start_bot())

update_table()
