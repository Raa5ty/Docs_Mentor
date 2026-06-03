from typing import List, Dict, Any
from urllib.parse import urljoin
from .base import BaseParser

class UniversalParser(BaseParser):
    """
    Универсальный парсер для любых сайтов документации.
    Не собирает страницы автоматически — пользователь передаёт список URL.
    """
    
    def __init__(self, base_url: str, page_urls: List[str] = None):
        """
        base_url: корневой URL документации
        page_urls: список URL страниц для парсинга (опционально)
        """
        super().__init__(base_url)
        self.page_urls = page_urls or []
    
    def set_page_urls(self, urls: List[str]) -> None:
        """Устанавливает список URL страниц для парсинга"""
        self.page_urls = urls
    
    def add_page_url(self, url: str) -> None:
        """Добавляет одну страницу в список"""
        if url not in self.page_urls:
            self.page_urls.append(url)
    
    def get_all_pages(self) -> List[str]:
        """
        Возвращает список страниц.
        Так как автоматический сбор не реализован,
        возвращаем то, что передал пользователь.
        """
        return self.page_urls
    
    def parse_page(self, url: str, html: str) -> Dict[str, Any]:
        """
        Извлекает заголовок и основной текст из любой HTML-страницы.
        Использует универсальные селекторы.
        """
        soup = self.parse_html(html)
        
        # Извлекаем заголовок
        title = None
        title_selectors = ['h1', 'title', '.title', '.page-title', '.post-title']
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            title = url.split('/')[-1].replace('.html', '').replace('-', ' ').replace('_', ' ').title()
        
        # Удаляем ненужные элементы
        for unwanted in soup.select('nav, .navbar, .sidebar, .menu, .footer, .copyright, script, style, [role="navigation"]'):
            unwanted.decompose()
        
        # Ищем основной контент по универсальным селекторам
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.post-content',
            '.documentation',
            '.docs-content',
            '.markdown-body',
            '.entry-content',
            'body'
        ]
        
        content = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem
                break
        
        if not content:
            content = soup.body
        
        if content is None:
            return {
                'title': title,
                'text': '',
                'metadata': {
                    'parser': 'UniversalParser',
                    'error': 'No content found',
                    'url': url
                }
            }
        
        # Удаляем оставшиеся скрипты и стили
        for unwanted in content.select('script, style'):
            unwanted.decompose()
        
        # Извлекаем текст
        text = content.get_text(separator='\n', strip=True)
        text = self.clean_text(text)
        
        metadata = {
            'parser': 'UniversalParser',
            'title': title,
            'source_url': url
        }
        
        return {
            'title': title,
            'text': text,
            'metadata': metadata
        }