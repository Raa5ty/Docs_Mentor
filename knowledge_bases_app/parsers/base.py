from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup

class BaseParser(ABC):
    """
    Абстрактный базовый класс для всех парсеров документации.
    Каждый парсер должен уметь:
    1. Получить список всех страниц документации
    2. Распарсить отдельную страницу (заголовок + текст)
    """
    
    def __init__(self, base_url: str):
        """
        base_url: корневой URL документации (например, https://fastapi.tiangolo.com)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DocsMentorBot/1.0 (Educational Project)'
        })
    
    def fetch_html(self, url: str) -> str:
        """
        Скачивает HTML-страницу и возвращает текст.
        Если ошибка — поднимает исключение.
        """
        response = self.session.get(url, timeout=30)
        response.raise_for_status()  # выбросит исключение при 404, 500 и т.д.
        return response.text
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Превращает HTML в объект BeautifulSoup для удобного поиска"""
        return BeautifulSoup(html, 'html.parser')
    
    @abstractmethod
    def get_all_pages(self) -> List[str]:
        """
        Возвращает список всех URL страниц документации.
        Должен быть реализован в каждом конкретном парсере.
        """
        pass
    
    @abstractmethod
    def parse_page(self, url: str, html: str) -> Dict[str, Any]:
        """
        Принимает URL и HTML страницы.
        Возвращает словарь с ключами:
        - 'title': заголовок страницы
        - 'text': основной текст страницы (очищенный от навигации, меню и т.д.)
        - 'metadata': дополнительная информация (секция, порядок и т.п.)
        """
        pass
    
    def get_page_text(self, url: str) -> Dict[str, Any]:
        """
        Полный цикл для одной страницы: скачать -> распарсить
        """
        html = self.fetch_html(url)
        return self.parse_page(url, html)
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от служебных символов и лишних пробелов"""
        import re
        text = re.sub(r'<[^>]+>', '', text)  # ← ЭТА СТРОКА УДАЛЯЕТ HTML-ТЕГИ
        text = text.replace('¶', '')
        text = text.replace('§', '')
        text = text.replace('©', '')
        text = text.replace('®', '')
        text = re.sub(r'\n\s*\n', '\n\n', text)  # нормализуем переносы строк
        text = re.sub(r'[ \t]+', ' ', text)       # нормализуем пробелы
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)