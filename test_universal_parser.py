from knowledge_bases_app.parsers.universal_parser import UniversalParser

# Пример: документация небольшой библиотеки
parser = UniversalParser("https://requests.readthedocs.io/en/latest/")

# Пользователь сам указывает нужные страницы
pages = [
    "https://requests.readthedocs.io/en/latest/user/quickstart/",
    "https://requests.readthedocs.io/en/latest/user/advanced/",
    "https://requests.readthedocs.io/en/latest/api/",
]

parser.set_page_urls(pages)

print("Универсальный парсер")
print(f"Страниц для парсинга: {len(parser.get_all_pages())}")
print()

for url in pages:
    print(f"Парсим: {url}")
    try:
        page_data = parser.get_page_text(url)
        print(f"  Заголовок: {page_data['title']}")
        print(f"  Длина текста: {len(page_data['text'])} символов")
        print(f"  Первые 200 символов: {page_data['text'][:200].replace(chr(10), ' ')}...")
        print()
    except Exception as e:
        print(f"  Ошибка: {e}")
        print()

print("="*60)
print("Демо парсинга конкретной страницы (FastAPI, но без автосбора)")
print()

parser2 = UniversalParser("https://fastapi.tiangolo.com/")
parser2.add_page_url("https://fastapi.tiangolo.com/tutorial/first-steps/")

url = parser2.get_all_pages()[0]
page_data = parser2.get_page_text(url)

print(f"URL: {url}")
print(f"Заголовок: {page_data['title']}")
print(f"Длина текста: {len(page_data['text'])} символов")
print(f"\nПервые 500 символов:\n{'-'*40}")
print(page_data['text'][:500])