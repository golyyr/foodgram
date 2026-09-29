from django.template import Context, Engine
from django.utils import timezone

SHOPPING_LIST_TEMPLATE = """
Список покупок
Дата составления: {{ date }}
{% if products %}
{% for product in products %}
{{ forloop.counter }}. {{ product.product__name|capfirst }} ({% spaceless %}
{{ product.product__measurement_unit }}
{% endspaceless %}) — {{ product.total }}
{% endfor %}
{% endif %}
{% if recipes %}
Рецепты:
{% for recipe in recipes %}
{% with author=recipe.author.username %}
{{ forloop.counter }}. {{ recipe.name }} (@{{ author }}) [{% spaceless %}
{% for tag in recipe.tags.all %}{{ tag.name }}{% if not forloop.last
%}, {% endif %}{% endfor %}{% endspaceless %}]
{% endwith %}
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
