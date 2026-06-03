from typing import List, Dict, Any
from urllib.parse import urljoin
from .base import BaseParser
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re

class SphinxParser(BaseParser):
    """
    Парсер для документации, построенной на Sphinx (PyTorch, Python docs)
    """
    
    def get_all_pages(self) -> List[str]:
        """
        Собирает все страницы документации.
        Приоритеты:
        1. sitemap.xml
        2. Навигация на главной странице
        """
        # Попробуем найти sitemap.xml в корне сайта
        sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        try:
            response = self.session.get(sitemap_url, timeout=10)
            if response.status_code == 200:
                pages = self._parse_sitemap(response.text)
                if pages:
                    # Фильтруем только страницы документации (не genindex, не py-modindex)
                    filtered_pages = [
                        p for p in pages 
                        if not p.endswith('/genindex.html') 
                        and not p.endswith('/py-modindex.html')
                        and not p.endswith('/versions.html')
                        and '/_static/' not in p
                        and '/_sources/' not in p
                    ]
                    if filtered_pages:
                        return filtered_pages
        except Exception as e:
            print(f"Sitemap error: {e}")
        
        # Если sitemap не найден, парсим навигацию
        return self._parse_navigation()
    
    def _parse_sitemap(self, content: str) -> List[str]:
        """Парсит XML sitemap и возвращает список URL"""
        pages = set()
        try:
            root = ET.fromstring(content)
            # Пространство имён sitemap
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            for loc in root.findall('.//sm:loc', ns):
                page_url = loc.text
                if page_url and self._is_relevant_page(page_url):
                    pages.add(page_url)
        except ET.ParseError:
            # Может быть HTML sitemap
            soup = self.parse_html(content)
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and not href.startswith('#'):
                    full_url = urljoin(self.base_url, href)
                    if self._is_relevant_page(full_url):
                        pages.add(full_url)
        
        return list(pages)
    
    def _parse_navigation(self) -> List[str]:
        """Парсит навигацию на главной странице"""
        homepage_html = self.fetch_html(self.base_url)
        soup = self.parse_html(homepage_html)
        
        pages = set()
        
        # Ищем ссылки на модули (torch.html, nn.html, etc.)
        module_links = soup.find_all('a', href=re.compile(r'\.html$'))
        for link in module_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if self._is_relevant_page(full_url):
                    pages.add(full_url)
        
        # Также ищем ссылки в папке generated/
        generated_links = soup.find_all('a', href=re.compile(r'/generated/'))
        for link in generated_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                if self._is_relevant_page(full_url):
                    pages.add(full_url)
        
        return list(pages)
    
    def _is_relevant_page(self, url: str) -> bool:
        """Проверяет, является ли URL страницей документации"""
        # Исключаем файлы и внешние ссылки
        excluded_patterns = [
            '.css', '.js', '.json', '.txt', '.pdf',
            'mailto:', 'tel:', '#',
            '/_static/', '/_sources/', '/_images/',
            '/genindex', '/py-modindex', '/versions.html',
            '/search.html', '/index.html#', '/contents.html'
        ]
        
        for pattern in excluded_patterns:
            if pattern in url:
                return False
        
        # Оставляем HTML страницы и страницы в папке generated/
        return url.endswith('.html') or '/generated/' in url
    
    def parse_page(self, url: str, html: str) -> Dict[str, Any]:
        """
        Извлекает заголовок и основной текст страницы Sphinx.
        """
        soup = self.parse_html(html)
        
        # Извлекаем заголовок
        title = None
        title_selectors = ['h1', 'title']
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            title = url.split('/')[-1].replace('.html', '').replace('-', ' ').title()
        
        # Удаляем ненужные элементы
        for unwanted in soup.select('nav, .sphinxsidebar, .wy-nav-side, .rst-footer, .footer, script, style, [role="navigation"]'):
            unwanted.decompose()
        
        # Ищем основной контент
        content_selectors = [
            'div.body',
            'div.document',
            'div.content',
            'main',
            'article',
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
                'metadata': {'parser': 'SphinxParser', 'error': 'No content found', 'url': url}
            }
        
        # Удаляем оставшиеся скрипты и стили внутри контента
        for unwanted in content.select('script, style'):
            unwanted.decompose()
        
        # Извлекаем текст
        text = content.get_text(separator='\n', strip=True)
        text = self.clean_text(text)
        
        # Ограничиваем размер текста
        if len(text) > 50000:
            text = text[:50000] + "..."
        
        metadata = {
            'parser': 'SphinxParser',
            'title': title,
            'source_url': url
        }
        
        return {
            'title': title,
            'text': text,
            'metadata': metadata
        }