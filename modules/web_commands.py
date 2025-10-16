"""
Модуль для работы с веб-сайтами и интернет-командами
"""

import re
import webbrowser
import logging
import requests
from typing import Tuple, Dict, List
from urllib.parse import quote_plus


class WebCommandProcessor:
    """Класс для обработки веб-команд и работы с сайтами"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Популярные сайты с их URL
        self.popular_sites = {
            'youtube': 'https://www.youtube.com',
            'ютуб': 'https://www.youtube.com',
            'google': 'https://www.google.com',
            'гугл': 'https://www.google.com',
            'gmail': 'https://mail.google.com',
            'почта': 'https://mail.google.com',
            'facebook': 'https://www.facebook.com',
            'фейсбук': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'инстаграм': 'https://www.instagram.com',
            'twitter': 'https://twitter.com',
            'твиттер': 'https://twitter.com',
            'vk': 'https://vk.com',
            'вконтакте': 'https://vk.com',
            'telegram': 'https://web.telegram.org',
            'телеграм': 'https://web.telegram.org',
            'whatsapp': 'https://web.whatsapp.com',
            'ватсап': 'https://web.whatsapp.com',
            'github': 'https://github.com',
            'гитхаб': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'стековерфлоу': 'https://stackoverflow.com',
            'wikipedia': 'https://ru.wikipedia.org',
            'википедия': 'https://ru.wikipedia.org',
            'yandex': 'https://yandex.ru',
            'яндекс': 'https://yandex.ru',
            'mail.ru': 'https://mail.ru',
            'мейл': 'https://mail.ru',
            'habr': 'https://habr.com',
            'хабр': 'https://habr.com',
            'netflix': 'https://netflix.com',
            'нетфликс': 'https://netflix.com',
            'amazon': 'https://amazon.com',
            'амазон': 'https://amazon.com',
            'aliexpress': 'https://aliexpress.com',
            'алиэкспресс': 'https://aliexpress.com',
            'ozon': 'https://ozon.ru',
            'озон': 'https://ozon.ru',
            'wildberries': 'https://wildberries.ru',
            'вайлдберриз': 'https://wildberries.ru'
        }
        
        # Паттерны команд
        self.command_patterns = {
            'open_site': [
                r'открой\s+сайт\s+(.+)',
                r'перейди\s+на\s+(.+)',
                r'открыть\s+(.+)',
                r'зайди\s+на\s+(.+)',
                r'открой\s+(.+)',
            ],
            'search_google': [
                r'найди\s+(.+)',
                r'поищи\s+(.+)',
                r'гугли\s+(.+)',
                r'поиск\s+(.+)',
                r'найти\s+(.+)',
                r'ищи\s+(.+)',
            ],
            'search_youtube': [
                r'найди\s+на\s+ютубе?\s+(.+)',
                r'поищи\s+на\s+youtube\s+(.+)',
                r'ютуб\s+(.+)',
                r'видео\s+(.+)',
            ],
            'search_wikipedia': [
                r'что\s+такое\s+(.+)',
                r'википедия\s+(.+)',
                r'расскажи\s+о\s+(.+)',
                r'информация\s+о\s+(.+)',
            ],
            'translate': [
                r'переведи\s+(.+)',
                r'перевод\s+(.+)',
                r'translate\s+(.+)',
            ],
            'weather': [
                r'погода\s+(.+)',
                r'какая\s+погода\s+(.+)',
                r'weather\s+(.+)',
            ],
            'news': [
                r'новости\s*(.+)?',
                r'что\s+нового\s*(.+)?',
                r'news\s*(.+)?',
            ]
        }
    
    def process_command(self, command: str) -> Tuple[bool, str]:
        """
        Обрабатывает веб-команду
        
        Args:
            command: Текст команды
            
        Returns:
            Tuple[handled, response]
        """
        command = command.lower().strip()
        
        # Проверяем каждый тип команды
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    return self._execute_command(command_type, match, command)
        
        return False, "Команда не распознана как веб-команда"
    
    def _execute_command(self, command_type: str, match: re.Match, full_command: str) -> Tuple[bool, str]:
        """Выполняет конкретную веб-команду"""
        
        try:
            if command_type == 'open_site':
                site_name = match.group(1).strip()
                return self._open_site(site_name)
            
            elif command_type == 'search_google':
                query = match.group(1).strip()
                return self._search_google(query)
            
            elif command_type == 'search_youtube':
                query = match.group(1).strip()
                return self._search_youtube(query)
            
            elif command_type == 'search_wikipedia':
                query = match.group(1).strip()
                return self._search_wikipedia(query)
            
            elif command_type == 'translate':
                text = match.group(1).strip()
                return self._translate_text(text)
            
            elif command_type == 'weather':
                location = match.group(1).strip()
                return self._get_weather(location)
            
            elif command_type == 'news':
                topic = match.group(1).strip() if match.group(1) else ""
                return self._get_news(topic)
            
            return False, f"Неизвестный тип веб-команды: {command_type}"
            
        except Exception as e:
            error_msg = f"Ошибка выполнения веб-команды '{command_type}': {e}"
            self.logger.error(error_msg)
            return True, error_msg
    
    def _open_site(self, site_name: str) -> Tuple[bool, str]:
        """Открывает сайт по имени"""
        try:
            site_name = site_name.lower().strip()
            
            # Проверяем популярные сайты
            if site_name in self.popular_sites:
                url = self.popular_sites[site_name]
                webbrowser.open(url)
                return True, f"Открываю {site_name}: {url}"
            
            # Проверяем, является ли это URL
            if site_name.startswith(('http://', 'https://')):
                webbrowser.open(site_name)
                return True, f"Открываю сайт: {site_name}"
            
            # Проверяем, содержит ли точку (домен)
            if '.' in site_name and ' ' not in site_name:
                url = f"https://{site_name}"
                webbrowser.open(url)
                return True, f"Открываю сайт: {url}"
            
            # Иначе ищем в Google
            return self._search_google(f"сайт {site_name}")
            
        except Exception as e:
            return False, f"Ошибка открытия сайта: {e}"
    
    def _search_google(self, query: str) -> Tuple[bool, str]:
        """Выполняет поиск в Google"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return True, f"Ищу в Google: {query}"
        except Exception as e:
            return False, f"Ошибка поиска в Google: {e}"
    
    def _search_youtube(self, query: str) -> Tuple[bool, str]:
        """Выполняет поиск на YouTube"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            return True, f"Ищу на YouTube: {query}"
        except Exception as e:
            return False, f"Ошибка поиска на YouTube: {e}"
    
    def _search_wikipedia(self, query: str) -> Tuple[bool, str]:
        """Выполняет поиск в Wikipedia"""
        try:
            encoded_query = quote_plus(query)
            url = f"https://ru.wikipedia.org/wiki/Special:Search?search={encoded_query}"
            webbrowser.open(url)
            return True, f"Ищу в Wikipedia: {query}"
        except Exception as e:
            return False, f"Ошибка поиска в Wikipedia: {e}"
    
    def _translate_text(self, text: str) -> Tuple[bool, str]:
        """Открывает Google Переводчик"""
        try:
            encoded_text = quote_plus(text)
            url = f"https://translate.google.com/?sl=auto&tl=ru&text={encoded_text}"
            webbrowser.open(url)
            return True, f"Перевожу: {text}"
        except Exception as e:
            return False, f"Ошибка перевода: {e}"
    
    def _get_weather(self, location: str) -> Tuple[bool, str]:
        """Открывает прогноз погоды"""
        try:
            encoded_location = quote_plus(f"погода {location}")
            url = f"https://www.google.com/search?q={encoded_location}"
            webbrowser.open(url)
            return True, f"Показываю погоду для: {location}"
        except Exception as e:
            return False, f"Ошибка получения погоды: {e}"
    
    def _get_news(self, topic: str = "") -> Tuple[bool, str]:
        """Открывает новости"""
        try:
            if topic:
                encoded_topic = quote_plus(f"новости {topic}")
                url = f"https://www.google.com/search?q={encoded_topic}&tbm=nws"
                return_msg = f"Показываю новости по теме: {topic}"
            else:
                url = "https://news.google.com"
                return_msg = "Открываю Google Новости"
            
            webbrowser.open(url)
            return True, return_msg
        except Exception as e:
            return False, f"Ошибка получения новостей: {e}"
    
    def get_popular_sites(self) -> Dict[str, str]:
        """Возвращает список популярных сайтов"""
        return self.popular_sites.copy()
    
    def add_custom_site(self, name: str, url: str) -> bool:
        """Добавляет пользовательский сайт"""
        try:
            self.popular_sites[name.lower()] = url
            self.logger.info(f"Добавлен сайт: {name} -> {url}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления сайта: {e}")
            return False
    
    def check_internet_connection(self) -> bool:
        """Проверяет подключение к интернету"""
        try:
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_help_text(self) -> str:
        """Возвращает справку по веб-командам"""
        
        help_text = """
🌐 Веб-команды и интернет:

🔍 Поиск:
• "Найди рецепт борща" - поиск в Google
• "Поищи на ютубе как готовить" - поиск на YouTube
• "Что такое искусственный интеллект" - поиск в Wikipedia

🌍 Открытие сайтов:
• "Открой YouTube" - популярные сайты
• "Перейди на Google" - быстрый доступ
• "Зайди на github.com" - любой URL
• "Открой сайт Хабр" - поиск сайта

🔧 Полезные команды:
• "Переведи hello world" - Google Переводчик
• "Погода в Москве" - прогноз погоды
• "Новости технологий" - поиск новостей

📱 Популярные сайты:
YouTube, Google, Gmail, VK, Telegram, GitHub,
Wikipedia, Яндекс, Хабр, Netflix, Amazon и др.
        """.strip()
        
        return help_text