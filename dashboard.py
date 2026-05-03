import streamlit as st
import pandas as pd

# إعداد واجهة اللوحة
st.set_page_config(page_title="TIMENN Cafe Dashboard", layout="wide")

st.title("🏎️ لوحة تحكم الدرايف ثرو - تايمن")

# البيانات التجريبية للمنتجات الأربعة
data = {
    "المنتج": ["قهوة لاتيه", "شاي بالنعناع", "كروسان", "كيك مادلين"],
    "السعر": ["18 SAR", "10 SAR", "15 SAR", "12 SAR"],
    "حالة الطلب": ["بانتظار العميل", "بانتظار العميل", "بانتظار العميل", "بانتظار العميل"]
}

df = pd.DataFrame(data)

st.subheader("مراقبة الطلبات الحالية")
st.table(df)

st.success("اللوحة تعمل الآن! الخطوة التالية هي ربطها ببوت تيليقرام.")
