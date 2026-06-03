from knowledge_bases_app.parsers.sphinx_parser import SphinxParser

# Используем stable версию без /2.12 в пути
parser = SphinxParser("https://docs.pytorch.org/docs/stable/")

print("Собираем страницы PyTorch документации...")
print("Это может занять 1-2 минуты...")
print()

try:
    pages = parser.get_all_pages()
    print(f"Найдено страниц: {len(pages)}")
    
    if pages:
        print(f"\nПервые 10 страниц (основные модули):")
        for i, page in enumerate(pages[:10], 1):
            # Показываем только относительный путь для краткости
            display_url = page.replace('https://docs.pytorch.org/docs/stable/', '')
            print(f"  {i}. {display_url}")
        
        print("\n" + "="*60)
        print("Парсим torch.html (основной модуль)...")
        print()
        
        # Парсим конкретную страницу, а не первую попавшуюся
        test_url = "https://docs.pytorch.org/docs/stable/torch.html"
        page_data = parser.get_page_text(test_url)
        
        print(f"Заголовок: {page_data['title']}")
        print(f"Длина текста: {len(page_data['text'])} символов")
        print(f"\nПервые 800 символов:\n{'-'*40}")
        print(page_data['text'][:800])
        print("-"*40)
    else:
        print("Страницы не найдены! Проверьте структуру сайта.")
        
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()