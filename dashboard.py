# --- إضافة ذاكرة للسلة ---
user_carts = {} 

# معالج اختيار الأصناف (يسمح بالإضافة المتكررة)
@dp.message(F.text.in_(["☕️ قهوة لاتيه", "🍃 شاي بالنعناع", "🥐 كروسان", "🧁 كيك مادلين"]))
async def add_to_cart(message: types.Message):
    user_id = message.from_user.id
    item = message.text
    
    # إضافة الصنف للسلة أو زيادة الكمية
    if user_id not in user_carts:
        user_carts[user_id] = {}
    
    user_carts[user_id][item] = user_carts[user_id].get(item, 0) + 1
    
    # عرض محتويات السلة الحالية للعميل
    cart_summary = "\n".join([f"• {k} (الكمية: {v})" for k, v in user_carts[user_id].items()])
    
    kb = [[types.KeyboardButton(text="✅ إنهاء الطلب وإرسال الموقع", request_location=True)],
          [types.KeyboardButton(text="➕ إضافة صنف آخر")]]
    
    markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"🛒 سلتك الحالية:\n{cart_summary}\n\nهل تود إضافة المزيد أم إتمام الطلب؟", reply_markup=markup)

# معالج الموقع (يقوم بتجميع السلة وإرسالها كطلب واحد)
@dp.message(F.location)
async def finalize_order(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_carts:
        # تجميع السلة في نص واحد
        order_details = ", ".join([f"{v}x {k}" for k, v in user_carts[user_id].items()])
        
        # (هنا نضع نفس كود حساب المسافة للفروع الذي استخدمناه سابقاً)
        # ... كود المسافة والتوجيه لشارع التلفزيون أو الخزان ...

        entry = {
            "العميل": message.from_user.first_name,
            "الطلب": order_details, # سيظهر هنا: 2x كيك مادلين، 1x قهوة لاتيه
            "الفرع": nearest_branch,
            "الوقت": pd.Timestamp.now().strftime('%H:%M:%S')
        }
        save_order(entry)
        
        # تفريغ السلة بعد النجاح
        del user_carts[user_id]
        await message.answer(f"✅ تم استلام طلبك المجمع لفرع **{nearest_branch}**!")
