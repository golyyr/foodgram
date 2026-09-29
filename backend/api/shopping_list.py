from django.template import Context, Engine
from django.utils import timezone


def render_shopping_list(products, recipes):
    """Формирует текст списка покупок с датой, продуктами и рецептами."""
    template = Engine.get_default().from_string(
        'Список покупок\n'
        'Дата составления: {{ date }}\n'
        '{% if products %}'
        '{% for product in products %}'
        '{{ forloop.counter }}. '
        '{{ product.product__name|capfirst }} '
        '({{ product.product__measurement_unit }}) — {{ product.total }}\n'
        '{% endfor %}'
        '{% else %}'
        'Список пуст.\n'
        '{% endif %}'
        '{% if recipes %}'
        '\nРецепты:\n'
        '{% for recipe in recipes %}'
        '{{ forloop.counter }}. {{ recipe.name }}\n'
        '{% endfor %}'
        '{% endif %}',
    )
    return template.render(Context({
        'date': timezone.localdate().isoformat(),
        'products': products,
        'recipes': recipes,
    }))
