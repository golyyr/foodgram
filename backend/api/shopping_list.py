from django.template import Context, Engine
from django.utils import timezone

SHOPPING_LIST_TEMPLATE = """
Список покупок
Дата составления: {{ date }}
{% if products %}
{% for product in products %}
{{ forloop.counter }}. {{ product.product__name|capfirst }} ({{ product.product__measurement_unit }}) — {{ product.total }}
{% endfor %}
{% endif %}
{% if recipes %}

Рецепты:
{% for recipe in recipes %}
{{ forloop.counter }}. {{ recipe.name }} (@{{ recipe.author.username }}) [{% for tag in recipe.tags.all %}{{ tag.name }}{% if not forloop.last %}, {% endif %}{% endfor %}]
{% endfor %}
{% endif %}
"""


def render_shopping_list(products, recipes):
    """Формирует текст списка покупок с датой, продуктами и рецептами."""
    return Engine.get_default().from_string(SHOPPING_LIST_TEMPLATE).render(
        Context({
            'date': timezone.localdate().isoformat(),
            'products': products,
            'recipes': recipes,
        }),
    )
