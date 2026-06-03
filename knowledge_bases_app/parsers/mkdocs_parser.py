from typing import List, Dict, Any
from urllib.parse import urljoin
from .base import BaseParser

class MkDocsParser(BaseParser):
    """
    Парсер для документации, построенной на MkDocs (FastAPI, MkDocs, Material for MkDocs)
    """
    
    def get_all_pages(self) -> List[str]:
        """
        Собирает все страницы документации, обходя навигацию.
        """
        # Скачиваем главную страницу
        homepage_html = self.fetch_html(self.base_url)
        soup = self.parse_html(homepage_html)
        
        # Ищем все ссылки в навигации
        # Material for MkDocs часто использует классы 'md-nav__link'
        nav_links = []
        
        # Пробуем разные варианты поиска навигации
        nav_selectors = [
            'nav.md-nav a',           # Material MkDocs
            '.md-nav__link',          # Альтернативный класс
            'nav a',                  # Простой MkDocs
            '.wy-menu a',             # ReadTheDocs тема (тоже MkDocs)
        ]
        
        for selector in nav_selectors:
            links = soup.select(selector)
            if links:
                nav_links = links
                break
        
        # Если не нашли навигацию, ищем все внутренние ссылки (запасной вариант)
        if not nav_links:
            all_links = soup.find_all('a', href=True)
            base_domain = self.base_url.replace('https://', '').replace('http://', '').split('/')[0]
            nav_links = [
                link for link in all_links 
                if base_domain in link.get('href', '') 
                and not link.get('href', '').startswith('#')
                and not link.get('href', '').startswith('mailto:')
            ]
        
        # Преобразуем относительные ссылки в абсолютные
        pages = set()
        for link in nav_links:
            href = link.get('href')
            if href and not href.startswith('#'):
                full_url = urljoin(self.base_url, href)
                # Убираем якоря (#section) из URL
                full_url = full_url.split('#')[0]
                pages.add(full_url)
        
        return list(pages)
    
    def parse_page(self, url: str, html: str) -> Dict[str, Any]:
        """
        Извлекает заголовок и основной текст страницы.
        """
        soup = self.parse_html(html)
        
        # Извлекаем заголовок страницы
        title = None
        title_selectors = ['h1', 'title', '.md-title']
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            title = url.split('/')[-2] or url.split('/')[-1] or "Untitled"
        
        # Извлекаем основной текст
        # Удаляем ненужные элементы (навигация, меню, футеры)
        for unwanted in soup.select('nav, .md-sidebar, .md-footer, .wy-menu, .rst-footer, script, style'):
            unwanted.decompose()
        
        # Ищем основной контент
        content_selectors = [
            'article.md-content',
            'div.md-content',
            'main',
            '.wy-nav-content',
            '.documentation',
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
        
        # Извлекаем текст
        text = content.get_text(separator='\n', strip=True)
        text = self.clean_text(text)
        
        # Метаданные
        metadata = {
            'parser': 'MkDocsParser',
            'title': title,
        }
        
        return {
            'title': title,
            'text': text,
            'metadata': metadata
        }