#!/usr/bin/env python3
"""
Пример использования улучшенного Jarvis с поддержкой Telegram
Демонстрирует основные возможности нового функционала
"""

import asyncio
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demo_telegram_features():
    """Демонстрация возможностей Telegram"""
    
    print("🤖 Демонстрация улучшенного Jarvis с поддержкой Telegram")
    print("=" * 60)
    
    try:
        # Импортируем модули
        from modules.telegram_bot_api import TelegramBotAPI
        from modules.telegram_ai_analyzer import TelegramAIAnalyzer
        from modules.telegram_contact_manager import TelegramContactManager
        from modules.telegram_scheduler import TelegramScheduler
        from modules.telegram_memory import TelegramMemory
        
        print("✅ Модули успешно импортированы")
        
        # 1. Демонстрация Bot API
        print("\n📱 1. Telegram Bot API")
        print("-" * 30)
        
        try:
            bot_api = TelegramBotAPI()
            bot_info = await bot_api.get_me()
            if bot_info:
                print(f"✅ Бот подключен: {bot_info.get('first_name', 'Unknown')}")
            else:
                print("⚠️ Bot API недоступен (проверьте токен)")
        except Exception as e:
            print(f"❌ Ошибка Bot API: {e}")
        
        # 2. Демонстрация AI анализатора
        print("\n🧠 2. AI Анализатор")
        print("-" * 30)
        
        try:
            ai_analyzer = TelegramAIAnalyzer()
            print(f"✅ AI анализатор: {'Доступен' if ai_analyzer.ai_available else 'Недоступен'}")
            
            # Тестовый анализ
            test_messages = [
                {"text": "Привет! Как дела?", "from": {"id": 123}, "date": 1640995200},
                {"text": "Отлично, спасибо! 👍", "from": {"id": 456}, "date": 1640995260},
                {"text": "Работаю над проектом", "from": {"id": 123}, "date": 1640995320}
            ]
            
            analysis = await ai_analyzer.analyze_chat_comprehensive(test_messages, "full")
            if analysis.get('success'):
                print("✅ Тестовый анализ выполнен успешно")
                print(f"   - Сообщений: {analysis.get('basic_stats', {}).get('total_messages', 0)}")
                print(f"   - Настроение: {analysis.get('sentiment', {}).get('overall_sentiment', 'unknown')}")
            else:
                print("⚠️ Ошибка анализа")
                
        except Exception as e:
            print(f"❌ Ошибка AI анализатора: {e}")
        
        # 3. Демонстрация управления контактами
        print("\n👥 3. Управление контактами")
        print("-" * 30)
        
        try:
            contact_manager = TelegramContactManager()
            
            # Добавляем тестовый контакт
            test_contact = {
                "id": "123456789",
                "first_name": "Иван",
                "last_name": "Петров",
                "username": "ivan_petrov",
                "type": "user"
            }
            
            contact_manager.add_contact(test_contact)
            print("✅ Тестовый контакт добавлен")
            
            # Поиск контактов
            search_results = contact_manager.search_contacts("Иван")
            print(f"✅ Найдено контактов: {len(search_results)}")
            
            # Статистика
            stats = contact_manager.get_contact_statistics()
            print(f"✅ Всего контактов: {stats.get('total_contacts', 0)}")
            
        except Exception as e:
            print(f"❌ Ошибка управления контактами: {e}")
        
        # 4. Демонстрация планировщика
        print("\n📅 4. Планировщик сообщений")
        print("-" * 30)
        
        try:
            scheduler = TelegramScheduler()
            
            # Планируем тестовое сообщение
            from datetime import datetime, timedelta
            future_time = datetime.now() + timedelta(minutes=1)
            
            message_id = scheduler.schedule_message(
                chat_id="test_chat",
                message="Тестовое сообщение",
                send_time=future_time
            )
            
            print(f"✅ Сообщение запланировано: {message_id}")
            
            # Получаем список запланированных сообщений
            scheduled = scheduler.get_scheduled_messages()
            print(f"✅ Запланировано сообщений: {len(scheduled)}")
            
            # Останавливаем планировщик
            scheduler.stop_scheduler()
            print("✅ Планировщик остановлен")
            
        except Exception as e:
            print(f"❌ Ошибка планировщика: {e}")
        
        # 5. Демонстрация памяти
        print("\n💭 5. Память разговоров")
        print("-" * 30)
        
        try:
            memory = TelegramMemory()
            
            # Добавляем тестовые сообщения
            memory.add_message("test_chat", "user1", "Привет всем!")
            memory.add_message("test_chat", "user2", "Привет! Как дела?")
            memory.add_message("test_chat", "user1", "Отлично, работаю над проектом")
            
            print("✅ Тестовые сообщения добавлены")
            
            # Получаем историю
            history = memory.get_conversation_history("test_chat", 10)
            print(f"✅ История загружена: {len(history)} сообщений")
            
            # Получаем контекст
            context = memory.get_context("test_chat")
            print(f"✅ Контекст: {len(context)} элементов")
            
            # Поиск
            search_results = memory.search_messages("проект")
            print(f"✅ Найдено сообщений: {len(search_results)}")
            
            # Резюме
            summary = memory.get_conversation_summary("test_chat")
            print(f"✅ Резюме: {summary.get('total_messages', 0)} сообщений")
            
        except Exception as e:
            print(f"❌ Ошибка памяти: {e}")
        
        print("\n🎉 Демонстрация завершена!")
        print("\n📋 Доступные команды:")
        print("• 'Открой Telegram' - запустить мессенджер")
        print("• 'Анализируй чат с ИИ' - полный AI анализ")
        print("• 'Резюме чата' - краткое описание")
        print("• 'Найди сообщения ключевое слово' - поиск")
        print("• 'Отправь через бота сообщение' - отправка через API")
        print("• 'Управление контактами' - работа с контактами")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите зависимости: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

def main():
    """Главная функция"""
    print("🚀 Запуск демонстрации Telegram функций...")
    
    try:
        # Запускаем асинхронную демонстрацию
        asyncio.run(demo_telegram_features())
    except KeyboardInterrupt:
        print("\n👋 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
