# locales.py
TEXTS = {
    'ru': {
        'welcome': (
            "👋 Привет! Я бот для создания стикерпаков из твоих фотографий.\n\n"
            "Отправь мне изображение (как фото или документ для лучшего качества), "
            "и я автоматически добавлю его в твой личный стикерпак!\n\n"
            "Команды:\n"
            "/start - Начать работу\n"
            "/help - Справка\n"
            "/language - Выбрать язык"
        ),
        'help': (
            "ℹ️ Как пользоваться:\n\n"
            "1. Отправь мне фото (как изображение или документ)\n"
            "2. Выбери режим обработки (удалить фон или оставить)\n"
            "3. Получи стикер и ссылку на свой стикерпак!\n\n"
            "Твой стикерпак будет автоматически создан при добавлении первого стикера."
        ),
        'choose_language': "🌐 Выберите язык / Choose language:",
        'language_changed': "✅ Язык изменён на русский",
        'send_photo': "📷 Пожалуйста, отправь мне изображение (фото или файл) для создания стикера",
        'choose_mode': "Выбери режим обработки:",
        'mode_remove_bg': "🎨 Вырезать фон",
        'mode_keep_bg': "🖼 Оставить фон",
        'processing': "⏳ Обрабатываю изображение...",
        'adding_sticker': "➕ Добавляю стикер в твой пак...",
        'success': "✅ Стикер добавлен!\n\n🔗 Твой стикерпак: {link}",
        'error_processing': "❌ Ошибка обработки изображения. Попробуй другое фото.",
        'error_telegram': "❌ Ошибка Telegram API: {error}",
        'error_general': "❌ Произошла ошибка. Попробуй ещё раз.",
        'pack_created': "🎉 Стикерпак создан!",
        'send_document': "💡 Совет: отправь изображение как документ для лучшего качества!",
        'callback_expired': "⚠️ Эта кнопка устарела. Отправь новое изображение!",
        'unknown_command': "❓ Неизвестная команда. Используй /help для справки",
    },
    'en': {
        'welcome': (
            "👋 Hello! I'm a bot that creates sticker packs from your photos.\n\n"
            "Send me an image (as photo or document for better quality), "
            "and I'll automatically add it to your personal sticker pack!\n\n"
            "Commands:\n"
            "/start - Start\n"
            "/help - Help\n"
            "/language - Choose language"
        ),
        'help': (
            "ℹ️ How to use:\n\n"
            "1. Send me a photo (as image or document)\n"
            "2. Choose processing mode (remove background or keep)\n"
            "3. Get your sticker and link to your sticker pack!\n\n"
            "Your sticker pack will be created automatically when you add the first sticker."
        ),
        'choose_language': "🌐 Выберите язык / Choose language:",
        'language_changed': "✅ Language changed to English",
        'send_photo': "📷 Please send me an image (photo or file) to create a sticker",
        'choose_mode': "Choose processing mode:",
        'mode_remove_bg': "🎨 Remove Background",
        'mode_keep_bg': "🖼 Keep Background",
        'processing': "⏳ Processing image...",
        'adding_sticker': "➕ Adding sticker to your pack...",
        'success': "✅ Sticker added!\n\n🔗 Your sticker pack: {link}",
        'error_processing': "❌ Error processing image. Try another photo.",
        'error_telegram': "❌ Telegram API error: {error}",
        'error_general': "❌ An error occurred. Try again.",
        'pack_created': "🎉 Sticker pack created!",
        'send_document': "💡 Tip: send image as document for better quality!",
        'callback_expired': "⚠️ This button is outdated. Send a new image!",
        'unknown_command': "❓ Unknown command. Use /help for assistance",
    }
}


def get_text(lang: str, key: str, **kwargs) -> str:
    """Get localized text by language and key."""
    text = TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'].get(key, ''))
    return text.format(**kwargs) if kwargs else text
