MESSAGES = {
    'en': {
        'product_not_found': 'Product not found',
    },
    'es': {
        'product_not_found': 'Producto no encontrado',
    },
}


def get_message(lang: str, key: str) -> str:
    lang_code = lang.split('-')[0]
    return MESSAGES.get(lang_code, MESSAGES['en']).get(key, key)
