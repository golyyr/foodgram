from django.utils import timezone


def _capfirst(value):
    text = str(value)
    return f'{text[:1].upper()}{text[1:]}' if text else text


def render_shopping_list(products, recipes):
    """Формирует текст списка покупок с датой, продуктами и рецептами."""
    lines = [
        'Список покупок',
        f'Дата составления: {timezone.localdate().isoformat()}',
    ]
    products = list(products)
    if products:
        for index, product in enumerate(products, start=1):
            lines.append(
                f'{index}. {_capfirst(product["product__name"])} '
                f'({product["product__measurement_unit"]}) — '
                f'{product["total"]}',
            )
    recipes = list(recipes)
    if recipes:
        lines.append('')
        lines.append('Рецепты:')
        for index, recipe in enumerate(recipes, start=1):
            tags = ', '.join(tag.name for tag in recipe.tags.all())
            lines.append(
                f'{index}. {recipe.name} '
                f'(@{recipe.author.username}) [{tags}]',
            )
    return '\n'.join(lines) + '\n'
