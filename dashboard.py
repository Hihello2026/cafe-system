import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. إعدادات الفروع ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
DB_FILE = "orders.csv"

# إحداثيات الفروع في الرياض
BRANCHES = {
    "شارع التلفزيون": (24.6475, 46.7042),
    "شارع الخزان": (24.6412, 46.7035)
}

st.set_page_config(page_title="TIMENN Multi-Branch", layout="wide", page_icon="🏎️")
st.title("🏎️ لوحة تايمن - إدارة الفروع الحية")

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
    st.subheader("سجل العمليات الحية (كافة الفروع)")
    if st.button("🔄 تحديث"):
        st.rerun()
    
    df_display = load_orders()
    if not df_display.empty:
        # ترتيب حسب الوقت الأحدث
        st.table(df_display.iloc[::-1])
    else:
        st.info("بانتظار وصول طلبات من الفروع...")

with col2:
    st.subheader("إحصائيات سريعة")
    if not df_display.empty:
        st.metric("إجمالي الطلبات", len(df_display))
        st.write("آخر تحديث:", pd.Timestamp.now().strftime('%H:%M'))

# --- 4. محرك البوت الذكي ---
user_selections = {}

async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه"), types.KeyboardButton(text="🧁 كيك مادلين")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع"), types.KeyboardButton(text="🥐 كروسان")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("مرحباً بك في تايمن! يرجى اختيار طلبك:", reply_markup=markup)

    @dp.message(F.text & ~F.text.startswith('/'))
    async def process_order(message: types.Message):
        user_selections[message.from_user.id] = message.text
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتحديد أقرب فرع", request_location=True)]]
        await message.answer(
            f"تم اختيار {message.text}. فضلاً أرسل موقعك لنقوم بتوجيه طلبك للفرع الأقرب (التلفزيون أو الخزان):", 
            reply_markup=types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True)
        )

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        order_item = user_selections.get(message.from_user.id, "طلب متنوع")
        u_coords = (message.location.latitude, message.location.longitude)
        
        # حساب المسافة لأقرب فرع تلقائياً
        distances = {name: geodesic(u_coords, coords).km for name, coords in BRANCHES.items()}
        nearest_branch = min(distances, key=distances.get)
        min_dist = distances[nearest_branch]
        
        entry = {
            "العميل": message.from_user.first_name,
            "الطلب": order_item,
            "الفرع": nearest_branch,
            "المسافة": f"{min_dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(entry)
        await message.answer(f"✅ تم! طلبك موجه لفرع **{nearest_branch}**. يبعد عنك {min_dist:.2f} كم.")

    await dp.start_polling(bot, handle_signals=False)

if st.button("🛰️ تفعيل نظام الفروع"):
    st.warning("نظام الرادار الموحد يعمل الآن...")
    try:
        asyncio.run(start_bot())
    except Exception as e:
        st.error(f"خطأ: {e}")
