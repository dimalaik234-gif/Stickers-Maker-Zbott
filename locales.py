# locales.py
TEXTS = {
    'ru': {
        'welcome': (
            "👋 Привет! Я бот для создания стикерпаков из твоих фотографий.\n\n"
            "✨ Возможности:\n"
            "🎨 Удаление фона с фотографий\n"
            "📦 Создание неограниченного количества стикерпаков\n"
            "🎭 Поддержка обычных стикеров и Custom Emoji\n"
            "😊 Выбор эмодзи для каждого стикера\n\n"
            "Команды:\n"
            "/start - Начать работу\n"
            "/packs - Мои стикерпаки\n"
            "/newpack - Создать новый пак\n"
            "/help - Справка\n"
            "/language - Выбрать язык"
        ),
        'help': (
            "ℹ️ Как пользоваться:\n\n"
            "1️⃣ Создай стикерпак командой /newpack\n"
            "2️⃣ Отправь мне фото (как изображение или документ)\n"
            "3️⃣ Выбери режим обработки (удалить фон или оставить)\n"
            "4️⃣ Выбери эмодзи для стикера\n"
            "5️⃣ Получи стикер и ссылку на свой стикерпак!\n\n"
            "📋 Команды:\n"
            "/packs - Список всех твоих паков\n"
            "/newpack - Создать новый стикерпак\n"
            "/language - Сменить язык"
        ),
        'choose_language': "🌐 Выберите язык / Choose language:",
        'language_changed': "✅ Язык изменён на русский",
        'send_photo': "📷 Отправь мне изображение для создания стикера",
        'choose_mode': "Выбери режим обработки:",
        'mode_remove_bg': "🎨 Вырезать фон",
        'mode_keep_bg': "🖼 Оставить фон",
        'processing': "⏳ Обрабатываю изображение...",
        'adding_sticker': "➕ Добавляю стикер в твой пак...",
        'success': "✅ Стикер добавлен!\n\n🔗 Твой стикерпак: {link}",
        'error_processing': "❌ Ошибка обработки изображения. Попробуй другое фото.",
        'error_telegram': "❌ Ошибка Telegram API: {error}",
        'error_general': "❌ Произошла ошибка. Попробуй ещё раз.",
        'callback_expired': "⚠️ Эта кнопка устарела. Отправь новое изображение!",
        'unknown_command': "❓ Неизвестная команда. Используй /help для справки",
        
        # Новые ключи
        'no_packs': "📭 У тебя пока нет стикерпаков.\n\nСоздай первый командой /newpack",
        'your_packs': "📦 Твои стикерпаки:\n\n",
        'pack_item': "{emoji} <b>{title}</b>\n├ Тип: {type}\n├ Ссылка: {link}\n└ Активен: {active}\n",
        'current_pack_set': "✅ Активный пак: <b>{title}</b>",
        'pack_type_regular': "Обычный",
        'pack_type_emoji': "Custom Emoji",
        'create_pack_name': "✏️ Введи название для стикерпака (латиницей, без пробелов):\n\nНапример: <code>my_cool_stickers</code>",
        'create_pack_title': "✏️ Теперь введи отображаемое название (любые символы):\n\nНапример: <code>Мои крутые стикеры</code>",
        'choose_pack_type': "🎭 Выбери тип стикерпака:",
        'pack_type_btn_regular': "📱 Обычные стикеры",
        'pack_type_btn_emoji': "🎭 Custom Emoji",
        'pack_created_success': "🎉 Стикерпак создан!\n\n📦 <b>{title}</b>\n🔗 {link}\n\nТеперь отправь фото для добавления первого стикера!",
        'pack_name_invalid': "❌ Неправильное название. Используй только латинские буквы, цифры и подчеркивания.\n\nПопробуй ещё раз:",
        'pack_exists': "❌ Пак с таким названием уже существует. Введи другое название:",
        'choose_emoji': "😊 Выбери эмодзи для этого стикера:",
        'custom_emoji_input': "✏️ Или отправь свой эмодзи текстом:",
        'emoji_set': "✅ Эмодзи установлен: {emoji}",
        'cancel': "❌ Отмена",
        'cancelled': "❌ Действие отменено",
        'select_pack': "📦 Выбери активный стикерпак:",
        'no_active_pack': "⚠️ У тебя нет активного стикерпака.\n\nСоздай новый командой /newpack или выбери существующий командой /packs",
    },
    'en': {
        'welcome': (
            "👋 Hello! I'm a bot that creates sticker packs from your photos.\n\n"
            "✨ Features:\n"
            "🎨 Background removal from photos\n"
            "📦 Create unlimited sticker packs\n"
            "🎭 Support for regular stickers and Custom Emoji\n"
            "😊 Choose emoji for each sticker\n\n"
            "Commands:\n"
            "/start - Start\n"
            "/packs - My sticker packs\n"
            "/newpack - Create new pack\n"
            "/help - Help\n"
            "/language - Choose language"
        ),
        'help': (
            "ℹ️ How to use:\n\n"
            "1️⃣ Create a sticker pack with /newpack\n"
            "2️⃣ Send me a photo (as image or document)\n"
            "3️⃣ Choose processing mode (remove background or keep)\n"
            "4️⃣ Choose emoji for the sticker\n"
            "5️⃣ Get your sticker and link to your sticker pack!\n\n"
            "📋 Commands:\n"
            "/packs - List all your packs\n"
            "/newpack - Create new sticker pack\n"
            "/language - Change language"
        ),
        'choose_language': "🌐 Выберите язык / Choose language:",
        'language_changed': "✅ Language changed to English",
        'send_photo': "📷 Send me an image to create a sticker",
        'choose_mode': "Choose processing mode:",
        'mode_remove_bg': "🎨 Remove Background",
        'mode_keep_bg': "🖼 Keep Background",
        'processing': "⏳ Processing image...",
        'adding_sticker': "➕ Adding sticker to your pack...",
        'success': "✅ Sticker added!\n\n🔗 Your sticker pack: {link}",
        'error_processing': "❌ Error processing image. Try another photo.",
        'error_telegram': "❌ Telegram API error: {error}",
        'error_general': "❌ An error occurred. Try again.",
        'callback_expired': "⚠️ This button is outdated. Send a new image!",
        'unknown_command': "❓ Unknown command. Use /help for assistance",
        
        # New keys
        'no_packs': "📭 You don't have any sticker packs yet.\n\nCreate your first one with /newpack",
        'your_packs': "📦 Your sticker packs:\n\n",
        'pack_item': "{emoji} <b>{title}</b>\n├ Type: {type}\n├ Link: {link}\n└ Active: {active}\n",
        'current_pack_set': "✅ Active pack: <b>{title}</b>",
        'pack_type_regular': "Regular",
        'pack_type_emoji': "Custom Emoji",
        'create_pack_name': "✏️ Enter sticker pack name (latin letters, no spaces):\n\nExample: <code>my_cool_stickers</code>",
        'create_pack_title': "✏️ Now enter display name (any characters):\n\nExample: <code>My Cool Stickers</code>",
        'choose_pack_type': "🎭 Choose sticker pack type:",
        'pack_type_btn_regular': "📱 Regular Stickers",
        'pack_type_btn_emoji': "🎭 Custom Emoji",
        'pack_created_success': "🎉 Sticker pack created!\n\n📦 <b>{title}</b>\n🔗 {link}\n\nNow send a photo to add your first sticker!",
        'pack_name_invalid': "❌ Invalid name. Use only latin letters, numbers and underscores.\n\nTry again:",
        'pack_exists': "❌ Pack with this name already exists. Enter another name:",
        'choose_emoji': "😊 Choose emoji for this sticker:",
        'custom_emoji_input': "✏️ Or send your emoji as text:",
        'emoji_set': "✅ Emoji set: {emoji}",
        'cancel': "❌ Cancel",
        'cancelled': "❌ Action cancelled",
        'select_pack': "📦 Select active sticker pack:",
        'no_active_pack': "⚠️ You don't have an active sticker pack.\n\nCreate a new one with /newpack or select existing with /packs",
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Get localized text by language and key."""
    text = TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'].get(key, ''))
    return text.format(**kwargs) if kwargs else text
