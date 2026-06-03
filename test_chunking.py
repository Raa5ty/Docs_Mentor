from knowledge_bases_app.chunking import chunk_page, count_tokens

# Тест с коротким текстом
short_page = {
    'title': 'Short Page',
    'text': 'Short text example. ' * 50,  # ~50 токенов
    'metadata': {'url': 'test.com'}
}

chunks = chunk_page(short_page, threshold_tokens=1500)
print(f"Короткая страница → {len(chunks)} чанк (не делим)")

# Тест с длинным текстом
long_text = 'Word ' * 2000  # много токенов
long_page = {
    'title': 'Long Page',
    'text': long_text,
    'metadata': {'url': 'test.com'}
}

total_tokens = count_tokens(long_text)
print(f"Длинная страница: {total_tokens} токенов")

chunks = chunk_page(long_page, threshold_tokens=1500)
print(f"Длинная страница → {len(chunks)} чанков")
for i, chunk in enumerate(chunks[:3]):
    print(f"  Чанк {i}: {chunk['token_count']} токенов")