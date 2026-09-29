from recipes.management.base_import import ImportJsonCommand
from recipes.models import Product


class Command(ImportJsonCommand):
    help = 'Импортирует продукты из JSON-фикстуры.'
    model = Product
    default_fixture = '/app/data/ingredients.json'
