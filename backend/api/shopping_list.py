from django.template import Context, Engine
from django.utils import timezone

SHOPPING_LIST_TEMPLATE = (
    'Список покупок\n'
    'Дата составления: {{ date }}\n'
    '{% if products %}\n'
    '  {% for product in products %}\n'
    '{{ forloop.counter }}. '
    '{{ product.product__name|capfirst }} '
    '({{ product.product__measurement_unit }}) — {{ product.total }}\n'
    '  {% endfor %}\n'
    '{% endif %}\n'
    '{% if recipes %}\n'
    'Рецепты:\n'
    '  {% for recipe in recipes %}\n'
    '{{ forloop.counter }}. {{ recipe.name }} '
    '(@{{ recipe.author.username }}) '
    '[{% for tag in recipe.tags.all %}'
    '{{ tag.name }}{% if not forloop.last %}, {% endif %}'
    '{% endfor %}]\n'
    '  {% endfor %}\n'
    '{% endif %}\n'
)


def render_shopping_list(products, recipes):
    """Формирует текст списка покупок с датой, продуктами и рецептами."""
    return Engine.get_default().from_string(SHOPPING_LIST_TEMPLATE).render(
        Context({
            'date': timezone.localdate().isoformat(),
            'products': products,
            'recipes': recipes,
        }),
    )
