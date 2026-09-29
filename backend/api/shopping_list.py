from django.template import Context, Engine
from django.utils import timezone


def render_shopping_list(products):
    """Формирует текст списка покупок с датой и нумерацией."""
    template = Engine.get_default().from_string(
        'Список покупок\n'
        'Дата составления: {{ date }}\n'
        '{% if products %}'
        '{% for product in products %}'
        '{{ forloop.counter }}. '
        '{{ product.name }} ({{ product.unit }}) — {{ product.total }}\n'
        '{% endfor %}'
        '{% else %}'
        'Список пуст.\n'
        '{% endif %}',
    )
    return template.render(Context({
        'date': timezone.localdate().isoformat(),
        'products': [
            {
                'name': row['product__name'].capitalize(),
                'unit': row['product__measurement_unit'],
                'total': row['total'],
            }
            for row in products
        ],
    }))
