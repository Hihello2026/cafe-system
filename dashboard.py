import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. الإعدادات الأساسية ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
BRANCHES = {
    "شارع التلفزيون": (24.6475, 46.7042),
    "شارع الخزان": (24.6412, 46.7035)
}
DB_FILE = "orders.csv"

# ذاكرة السلة (يجب تعريفها في أعلى الملف)
if 'user_carts' not in globals():
    user_carts = {}

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

# --- 3. واجهة Streamlit ---
st.set_page_config(page_title="TIMENN Dashboard", layout="wide", page_icon="🏎️")
st.title("🏎️ لوحة تايمن - نظام الفروع والسلال المتعددة")

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🔄 تحديث الجدول"): st.rerun()
    df_display = load_orders()
    if not df_display.empty: st.table(df_display.iloc[::-1])
    else: st.info("بانتظار الطلبات...")

# --- 4. محرك البوت (الترتيب الصحيح) ---
async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher() # تعريف dp هنا أولاً قبل استخدامه

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه"), types.KeyboardButton(text="🧁 كيك مادلين")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع"), types.KeyboardButton(text="🥐 كروسان")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("أهلاً بك في تايمن! اختر الأصناف التي تريدها (يمكنك اختيار أكثر من صنف):", reply_markup=markup)

    # معالج إضافة الأصناف للسلة
    @dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
    async def add_to_cart(message: types.Message):
        user_id = message.from_user.id
        item = message.text
        
        if user_id not in user_carts:
            user_carts[user_id] = {}
        
        user_carts[user_id][item] = user_carts[user_id].get(item, 0) + 1
        
        cart_summary = "\n".join([f"• {k} (الكمية: {v})" for k, v in user_carts[user_id].items()])
        
        kb = [
            [types.KeyboardButton(text="📍 إنهاء الطلب وإرسال الموقع", request_location=True)],
            [types.KeyboardButton(text="➕ إضافة صنف آخر")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer(f"🛒 سلتك الحالية:\n{cart_summary}\n\nأضف صنفاً آخر أو أرسل موقعك لإتمام الطلب:", reply_markup=markup)

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        user_id = message.from_user.id
        if user_id in user_carts and user_carts[user_id]:
            # تجميع السلة
            order_details = ", ".join([f"{v}x {k}" for k, v in user_carts[user_id].items()])
            u_coords = (message.location.latitude, message.location.longitude)
            
            # حساب أقرب فرع
            distances = {name: geodesic(u_coords, coords).km for name, coords in BRANCHES.items()}
            nearest_branch = min(distances, key=distances.get)
            min_dist = distances[nearest_branch]
            
            entry = {
                "العميل": message.from_user.first_name,
                "الطلب": order_details,
                "الفرع": nearest_branch,
                "المسافة": f"{min_dist:.2f} كم",
                "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
            }
            save_order(entry)
            
            # تصفير السلة بعد النجاح
            user_carts[user_id] = {}
            await message.answer(f"✅ تم استلام طلبك المجمع لفرع **{nearest_branch}**! ننتظرك بكل ود.")
        else:
            await message.answer("عذراً، سلتك فارغة! يرجى اختيار صنف أولاً.")

    await dp.start_polling(bot, handle_signals=False)

# --- 5. التشغيل ---
if st.button("🛰️ تفعيل نظام تايمن المطور"):
    st.warning("الرادار يعمل الآن.. جرب طلب عدة أصناف في تيليقرام.")
    try:
        asyncio.run(start_bot())
    except Exception as e:
        st.error(f"تنبيه: تأكد من إغلاق أي نافذة أخرى للبوت. الخطأ: {e}")
