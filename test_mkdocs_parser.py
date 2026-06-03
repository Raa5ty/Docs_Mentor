from knowledge_bases_app.parsers.mkdocs_parser import MkDocsParser

# Тестируем на FastAPI документации
parser = MkDocsParser("https://fastapi.tiangolo.com")

print("Собираем страницы...")
pages = parser.get_all_pages()
print(f"Найдено страниц: {len(pages)}")
print(f"Первые 5 страниц: {pages[:5]}")

print("\nПарсим первую страницу...")
test_url = "https://fastapi.tiangolo.com/tutorial/first-steps/"
page_data = parser.get_page_text(test_url)

print(f"Заголовок: {page_data['title']}")
print(f"Длина текста: {len(page_data['text'])} символов")
print(f"Первые 500 символов:\n{page_data['text'][:1000]}")