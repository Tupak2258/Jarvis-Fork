"""
Модуль для планирования отправки сообщений в Telegram
Обеспечивает отложенную отправку сообщений по расписанию
"""

import json
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import schedule


class TelegramScheduler:
    """Класс для планирования отправки сообщений в Telegram"""
    
    def __init__(self, bot_api=None, data_dir: str = "data"):
        self.logger = logging.getLogger(__name__)
        self.bot_api = bot_api
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Файл для хранения запланированных сообщений
        self.scheduled_messages_file = self.data_dir / "scheduled_messages.json"
        
        # Список запланированных сообщений
        self.scheduled_messages = {}
        
        # Флаг работы планировщика
        self.is_running = False
        self.scheduler_thread = None
        
        # Загружаем данные
        self._load_scheduled_messages()
        
        # Запускаем планировщик
        self.start_scheduler()
        
        self.logger.info("TelegramScheduler инициализирован")
    
    def _load_scheduled_messages(self):
        """Загружает запланированные сообщения из файла"""
        try:
            if self.scheduled_messages_file.exists():
                with open(self.scheduled_messages_file, 'r', encoding='utf-8') as f:
                    self.scheduled_messages = json.load(f)
            
            self.logger.info(f"Загружено {len(self.scheduled_messages)} запланированных сообщений")
        
        except Exception as e:
            self.logger.error(f"Ошибка загрузки запланированных сообщений: {e}")
    
    def _save_scheduled_messages(self):
        """Сохраняет запланированные сообщения в файл"""
        try:
            with open(self.scheduled_messages_file, 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_messages, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Запланированные сообщения сохранены")
        
        except Exception as e:
            self.logger.error(f"Ошибка сохранения запланированных сообщений: {e}")
    
    def schedule_message(self, chat_id: str, message: str, 
                        send_time: datetime, 
                        repeat: str = None,
                        message_id: str = None) -> str:
        """
        Планирует отправку сообщения
        
        Args:
            chat_id: ID чата для отправки
            message: Текст сообщения
            send_time: Время отправки
            repeat: Повторение (daily, weekly, monthly)
            message_id: ID сообщения (если не указан, генерируется)
        
        Returns:
            ID запланированного сообщения
        """
        try:
            if not message_id:
                message_id = f"msg_{int(time.time())}_{hash(message) % 10000}"
            
            # Проверяем, что время в будущем
            if send_time <= datetime.now():
                raise ValueError("Время отправки должно быть в будущем")
            
            scheduled_message = {
                'id': message_id,
                'chat_id': chat_id,
                'message': message,
                'send_time': send_time.isoformat(),
                'repeat': repeat,
                'created_at': datetime.now().isoformat(),
                'status': 'scheduled',
                'attempts': 0,
                'max_attempts': 3
            }
            
            self.scheduled_messages[message_id] = scheduled_message
            self._save_scheduled_messages()
            
            self.logger.info(f"Сообщение {message_id} запланировано на {send_time}")
            return message_id
        
        except Exception as e:
            self.logger.error(f"Ошибка планирования сообщения: {e}")
            raise
    
    def schedule_recurring_message(self, chat_id: str, message: str, 
                                  time_str: str, repeat: str) -> str:
        """
        Планирует повторяющееся сообщение
        
        Args:
            chat_id: ID чата
            message: Текст сообщения
            time_str: Время в формате "HH:MM"
            repeat: Повторение (daily, weekly, monthly)
        
        Returns:
            ID запланированного сообщения
        """
        try:
            message_id = f"recurring_{int(time.time())}_{hash(message) % 10000}"
            
            # Парсим время
            hour, minute = map(int, time_str.split(':'))
            
            # Создаем задачу для повторения
            if repeat == 'daily':
                schedule.every().day.at(time_str).do(
                    self._send_scheduled_message, message_id, chat_id, message
                )
            elif repeat == 'weekly':
                schedule.every().monday.at(time_str).do(
                    self._send_scheduled_message, message_id, chat_id, message
                )
            elif repeat == 'monthly':
                # Для месячного повторения используем первый день месяца
                schedule.every().month.do(
                    self._send_scheduled_message, message_id, chat_id, message
                )
            else:
                raise ValueError(f"Неподдерживаемое повторение: {repeat}")
            
            scheduled_message = {
                'id': message_id,
                'chat_id': chat_id,
                'message': message,
                'time_str': time_str,
                'repeat': repeat,
                'created_at': datetime.now().isoformat(),
                'status': 'scheduled',
                'type': 'recurring'
            }
            
            self.scheduled_messages[message_id] = scheduled_message
            self._save_scheduled_messages()
            
            self.logger.info(f"Повторяющееся сообщение {message_id} запланировано")
            return message_id
        
        except Exception as e:
            self.logger.error(f"Ошибка планирования повторяющегося сообщения: {e}")
            raise
    
    def cancel_message(self, message_id: str) -> bool:
        """
        Отменяет запланированное сообщение
        
        Args:
            message_id: ID сообщения
        
        Returns:
            True если сообщение отменено
        """
        try:
            if message_id in self.scheduled_messages:
                self.scheduled_messages[message_id]['status'] = 'cancelled'
                self.scheduled_messages[message_id]['cancelled_at'] = datetime.now().isoformat()
                self._save_scheduled_messages()
                
                self.logger.info(f"Сообщение {message_id} отменено")
                return True
            else:
                self.logger.warning(f"Сообщение {message_id} не найдено")
                return False
        
        except Exception as e:
            self.logger.error(f"Ошибка отмены сообщения: {e}")
            return False
    
    def get_scheduled_messages(self, chat_id: str = None) -> List[Dict[str, Any]]:
        """
        Получает список запланированных сообщений
        
        Args:
            chat_id: ID чата для фильтрации (опционально)
        
        Returns:
            Список запланированных сообщений
        """
        try:
            messages = list(self.scheduled_messages.values())
            
            if chat_id:
                messages = [msg for msg in messages if msg.get('chat_id') == chat_id]
            
            # Сортируем по времени отправки
            messages.sort(key=lambda x: x.get('send_time', ''))
            
            return messages
        
        except Exception as e:
            self.logger.error(f"Ошибка получения запланированных сообщений: {e}")
            return []
    
    def get_message_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Получает статус сообщения"""
        return self.scheduled_messages.get(message_id)
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Планировщик запущен")
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Планировщик остановлен")
    
    def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                # Проверяем запланированные сообщения
                self._check_scheduled_messages()
                
                # Запускаем schedule
                schedule.run_pending()
                
                # Пауза между проверками
                time.sleep(1)
            
            except Exception as e:
                self.logger.error(f"Ошибка в цикле планировщика: {e}")
                time.sleep(5)
    
    def _check_scheduled_messages(self):
        """Проверяет и отправляет запланированные сообщения"""
        try:
            current_time = datetime.now()
            
            for message_id, message_data in self.scheduled_messages.items():
                if message_data.get('status') != 'scheduled':
                    continue
                
                send_time_str = message_data.get('send_time')
                if not send_time_str:
                    continue
                
                try:
                    send_time = datetime.fromisoformat(send_time_str)
                    
                    # Проверяем, пора ли отправлять
                    if current_time >= send_time:
                        self._send_scheduled_message(message_id)
                
                except ValueError as e:
                    self.logger.warning(f"Неверный формат времени для сообщения {message_id}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Ошибка проверки запланированных сообщений: {e}")
    
    def _send_scheduled_message(self, message_id: str, chat_id: str = None, message: str = None):
        """Отправляет запланированное сообщение"""
        try:
            message_data = self.scheduled_messages.get(message_id)
            if not message_data:
                self.logger.warning(f"Данные сообщения {message_id} не найдены")
                return
            
            # Используем переданные параметры или данные из файла
            if chat_id is None:
                chat_id = message_data.get('chat_id')
            if message is None:
                message = message_data.get('message')
            
            if not chat_id or not message:
                self.logger.error(f"Неполные данные для сообщения {message_id}")
                return
            
            # Отправляем сообщение
            if self.bot_api:
                # Асинхронная отправка через Bot API
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    success = loop.run_until_complete(
                        self.bot_api.send_message(chat_id, message)
                    )
                    
                    if success:
                        message_data['status'] = 'sent'
                        message_data['sent_at'] = datetime.now().isoformat()
                        self.logger.info(f"Запланированное сообщение {message_id} отправлено")
                    else:
                        self._handle_send_failure(message_id)
                
                finally:
                    loop.close()
            
            else:
                # Fallback - просто помечаем как отправленное
                message_data['status'] = 'sent'
                message_data['sent_at'] = datetime.now().isoformat()
                self.logger.info(f"Запланированное сообщение {message_id} помечено как отправленное (Bot API недоступен)")
            
            # Обновляем данные
            self._save_scheduled_messages()
        
        except Exception as e:
            self.logger.error(f"Ошибка отправки запланированного сообщения {message_id}: {e}")
            self._handle_send_failure(message_id)
    
    def _handle_send_failure(self, message_id: str):
        """Обрабатывает неудачную отправку"""
        try:
            message_data = self.scheduled_messages.get(message_id)
            if not message_data:
                return
            
            message_data['attempts'] = message_data.get('attempts', 0) + 1
            message_data['last_attempt'] = datetime.now().isoformat()
            
            max_attempts = message_data.get('max_attempts', 3)
            
            if message_data['attempts'] >= max_attempts:
                message_data['status'] = 'failed'
                message_data['failed_at'] = datetime.now().isoformat()
                self.logger.error(f"Сообщение {message_id} не удалось отправить после {max_attempts} попыток")
            else:
                # Планируем повторную попытку через 5 минут
                retry_time = datetime.now() + timedelta(minutes=5)
                message_data['send_time'] = retry_time.isoformat()
                self.logger.warning(f"Повторная попытка отправки сообщения {message_id} через 5 минут")
            
            self._save_scheduled_messages()
        
        except Exception as e:
            self.logger.error(f"Ошибка обработки неудачной отправки: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику планировщика"""
        try:
            total_messages = len(self.scheduled_messages)
            
            status_counts = {}
            for message_data in self.scheduled_messages.values():
                status = message_data.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Статистика по типам повторения
            repeat_counts = {}
            for message_data in self.scheduled_messages.values():
                repeat = message_data.get('repeat')
                if repeat:
                    repeat_counts[repeat] = repeat_counts.get(repeat, 0) + 1
            
            return {
                'total_messages': total_messages,
                'status_counts': status_counts,
                'repeat_counts': repeat_counts,
                'last_updated': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def cleanup_old_messages(self, days: int = 30):
        """Очищает старые сообщения"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            
            old_messages = []
            for message_id, message_data in self.scheduled_messages.items():
                created_at = message_data.get('created_at', '')
                if created_at < cutoff_iso and message_data.get('status') in ['sent', 'failed', 'cancelled']:
                    old_messages.append(message_id)
            
            for message_id in old_messages:
                del self.scheduled_messages[message_id]
            
            if old_messages:
                self._save_scheduled_messages()
                self.logger.info(f"Удалено {len(old_messages)} старых сообщений")
        
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых сообщений: {e}")
    
    def __del__(self):
        """Деструктор - останавливает планировщик"""
        self.stop_scheduler()
