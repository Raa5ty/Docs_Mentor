"""
Модуль для разбивки текста на чанки с учётом токенов.
Использует cl100k_base (токенизация для text-embedding-3-small)
"""

import tiktoken
from typing import List, Dict, Any

def get_encoding():
    """Возвращает encoding для моделей OpenAI (cl100k_base)"""
    return tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Подсчитывает количество токенов для модели эмбеддингов"""
    encoding = get_encoding()
    return len(encoding.encode(text))

def split_text_into_chunks(
    text: str,
    max_tokens: int = 800,
    overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Разбивает текст на чанки с перекрытием.
    Используется ТОЛЬКО для длинных текстов (>1500 токенов)
    """
    encoding = get_encoding()
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return [{
            'text': text,
            'token_count': len(tokens),
            'start_index': 0,
            'end_index': len(tokens)
        }]
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        
        chunks.append({
            'text': chunk_text,
            'token_count': len(chunk_tokens),
            'start_index': start,
            'end_index': end
        })
        
        start += max_tokens - overlap
        
        if start >= len(tokens):
            break
    
    return chunks

def chunk_page(
    page_data: Dict[str, Any],
    max_tokens: int = 800,
    overlap: int = 150,
    threshold_tokens: int = 1500
) -> List[Dict[str, Any]]:
    """
    Принимает результат парсера и возвращает список чанков.
    
    Правила:
    - Если текст < threshold_tokens токенов → 1 чанк (не делим)
    - Если текст >= threshold_tokens → разбиваем на чанки
    
    TODO: В следующих версиях — разбивка по секциям (h1, h2, h3)
    """
    text = page_data['text']
    title = page_data.get('title', '')
    metadata = page_data.get('metadata', {})
    
    total_tokens = count_tokens(text)
    
    # Короткий текст — один чанк, не делим
    if total_tokens <= threshold_tokens:
        return [{
            'text': text,
            'token_count': total_tokens,
            'title': title,
            'chunk_index': 0,
            'total_chunks': 1,
            'is_full_page': True,
            'metadata': metadata
        }]
    
    # Длинный текст — разбиваем
    raw_chunks = split_text_into_chunks(text, max_tokens, overlap)
    
    result = []
    for i, chunk in enumerate(raw_chunks):
        result.append({
            'text': chunk['text'],
            'token_count': chunk['token_count'],
            'title': title,
            'chunk_index': i,
            'total_chunks': len(raw_chunks),
            'is_full_page': False,
            'metadata': metadata
        })
    
    return result