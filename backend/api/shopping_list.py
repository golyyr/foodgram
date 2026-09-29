from django.template import Context, Engine
from django.utils import timezone

SHOPPING_LIST_TEMPLATE = """
Список покупок
Дата составления: {{ date }}
{% if products %}
{% for product in products %}
{% with n=product.product__name %}
{% with u=product.product__measurement_unit %}
{{ forloop.counter }}. {{ n|capfirst }} ({{ u }}) — {{ product.total }}
{% endwith %}
{% endwith %}
{% endfor %}
{% endif %}
{% if recipes %}
Рецепты:
{% for recipe in recipes %}
{% with a=recipe.author.username %}
{{ forloop.counter }}. {{ recipe.name }} (@{{ a }}) [{% spaceless %}
{% for t in recipe.tags.all %}{% if not forloop.first %}, {% endif %}
{{ t.name }}{% endfor %}{% endspaceless %}]
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
