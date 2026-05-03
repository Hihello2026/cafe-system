import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
CAFE_LOCATION = (24.7136, 46.6753) # إحداثيات الرياض
DB_FILE = "orders.csv"

st.set_page_config(page_title="TIMENN Dashboard", layout="wide", page_icon="🏎️")
st.title("🏎️ لوحة تايمن - المراقبة الحية")

# --- 2. إدارة البيانات ---
def save_order(entry):
    df = pd.DataFrame([entry])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False)
    else:
        df.to_csv(DB_FILE, mode='a', header=False, index=False)

def load_orders():
    if os.path.isfile(DB_FILE):
        try: return pd.read_csv(DB_FILE)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 3. واجهة المستخدم ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("سجل العمليات")
    if st.button("🔄 تحديث الجدول"):
        st.rerun()
    
    df = load_orders()
    if not df.empty:
        st.table(df.iloc[::-1])
    else:
        st.info("بانتظار إشارات العملاء... (اضغط تحديث بعد إرسال الموقع)")

with col2:
    st.subheader("التحكم")
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- 4. محرك البوت ---
async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        # قائمة الأصناف
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("أهلاً بك في تايمن! اختر صنفك المفضل:", reply_markup=markup)

    # مستشعر مرن: يستجيب إذا احتوت الرسالة على أي من هذه الكلمات
    @dp.message(lambda msg: any(word in msg.text for word in ["قهوة", "شاي", "كروسان", "كيك", "مادلين", "لاتيه"]))
    async def ask_location(message: types.Message):
        # حفظ الطلب في الجلسة
        st.session_state['current_order'] = message.text
        
        # إنشاء زر الموقع
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        await message.answer(
            f"اختيار رائع: {message.text}\n\nفضلاً اضغط على الزر أدناه لمشاركة موقعك لنبدأ التحضير فوراً:", 
            reply_markup=types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True, one_time_keyboard=True)
        )

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        order_item = st.session_state.get('current_order', "طلب متنوع")
        
        # حساب المسافة
        u_coords = (message.location.latitude, message.location.longitude)
        dist = geodesic(u_coords, CAFE_LOCATION).km
        
        entry = {
            "العميل": message.from_user.first_name,
            "الطلب": order_item,
            "المسافة": f"{dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(entry)
        await message.answer("✅ تم استلام طلبك! سيظهر الآن في لوحة المقهى.")

    await dp.start_polling(bot, handle_signals=False)

# --- 5. التشغيل ---
if st.button("🛰️ تفعيل الرادار"):
    st.warning("الرادار يعمل الآن.. استقبل الطلب في تيليقرام ثم اضغط 'تحديث'")
    asyncio.run(start_bot())
