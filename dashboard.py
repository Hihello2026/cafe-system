import streamlit as st
import pandas as pd
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from geopy.distance import geodesic

# --- 1. الإعدادات ---
API_TOKEN = '8734967078:AAGLMX5luI5i6DBhr6Dks6VQJ0pHXdVpr1I'
# إحداثيات الفروع التي حددتها
BRANCHES = {
    "شارع التلفزيون": (24.6475, 46.7042),
    "شارع الخزان": (24.6412, 46.7035)
}
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
    st.subheader("سجل العمليات الحية")
    if st.button("🔄 تحديث الجدول"):
        st.rerun()
    
    df_display = load_orders()
    if not df_display.empty:
        st.table(df_display.iloc[::-1])
    else:
        st.info("بانتظار إشارات العملاء... (اضغط تحديث بعد استلام تأكيد البوت)")

with col2:
    st.subheader("التحكم")
    if st.button("🗑️ تصفير السجل"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.rerun()

# --- 4. محرك البوت (نسخة الاستجابة السريعة) ---
# ذاكرة مؤقتة لربط المستخدم بالطلب المختار
user_cache = {}

async def start_bot():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        # قائمة الأصناف كما هي في TIMENN
        kb = [
            [types.KeyboardButton(text="☕️ قهوة لاتيه")],
            [types.KeyboardButton(text="🍃 شاي بالنعناع")],
            [types.KeyboardButton(text="🥐 كروسان")],
            [types.KeyboardButton(text="🧁 كيك مادلين")]
        ]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("أهلاً بك في تايمن! اختر صنفك المفضل:", reply_markup=markup)

    # معالج "صيد" أي نص مرسل لضمان الرد الفوري
    @dp.message(F.text & ~F.text.startswith('/'))
    async def handle_any_text(message: types.Message):
        # حفظ الاختيار فوراً
        user_cache[message.from_user.id] = message.text
        
        # إنشاء زر الموقع
        loc_kb = [[types.KeyboardButton(text="📍 إرسال الموقع لتجهيز الطلب", request_location=True)]]
        markup = types.ReplyKeyboardMarkup(keyboard=loc_kb, resize_keyboard=True, one_time_keyboard=True)
        
        await message.answer(
            f"اختيار رائع: {message.text}\n\nفضلاً شاركنا موقعك الآن لنبدأ التحضير فوراً:", 
            reply_markup=markup
        )

    @dp.message(F.location)
    async def handle_location(message: types.Message):
        order_item = user_cache.get(message.from_user.id, "طلب متنوع")
        u_coords = (message.location.latitude, message.location.longitude)
        
        # حساب المسافات للفروع المختارة
        dist_tel = geodesic(u_coords, BRANCHES["شارع التلفزيون"]).km
        dist_khz = geodesic(u_coords, BRANCHES["شارع الخزان"]).km
        
        # تحديد الأقرب
        if dist_tel < dist_khz:
            branch, dist = "شارع التلفزيون", dist_tel
        else:
            branch, dist = "شارع الخزان", dist_khz
        
        entry = {
            "العميل": message.from_user.first_name,
            "الطلب": order_item,
            "الفرع": branch,
            "المسافة": f"{dist:.2f} كم",
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(entry)
        await message.answer(f"✅ تم استلام طلبك لفرع **{branch}**! ستجده جاهزاً عند وصولك.")

    # تشغيل البوت بدون تداخل مع إشارات النظام
    await dp.start_polling(bot, handle_signals=False)

# --- 5. التشغيل ---
if st.button("🛰️ تفعيل الرادار"):
    st.warning("الرادار يعمل الآن.. جرب إرسال طلب من تيليقرام.")
    try:
        # تشغيل الحدث بشكل مباشر لضمان عدم التعليق
        asyncio.run(start_bot())
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
