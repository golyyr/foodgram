from django.utils import timezone
from django.utils.formats import date_format
from django.utils.text import capfirst

PRODUCT_LINE = '{}. {} ({}) — {}'
RECIPE_LINE = '{}. {} (@{}) [{}]'


def render_shopping_list(products, recipes):
    """Формирует текст списка покупок с датой, продуктами и рецептами."""
    lines = [
        'Список покупок',
        'Дата составления: {}'.format(
            date_format(timezone.localdate(), 'd E Y'),
        ),
        *[
            PRODUCT_LINE.format(
                index,
                capfirst(product['product__name']),
                product['product__measurement_unit'],
                product['total'],
            )
            for index, product in enumerate(products, start=1)
        ],
    ]
    if recipes:
        lines += [
            '',
            'Рецепты:',
            *[
                RECIPE_LINE.format(
                    index,
                    recipe.name,
                    recipe.author.username,
                    ', '.join(tag.name for tag in recipe.tags.all()),
                )
                for index, recipe in enumerate(recipes, start=1)
            ],
        ]
    return '\n'.join(lines) + '\n'
