from recipes.management.base_import import ImportJsonCommand
from recipes.models import Tag


class Command(ImportJsonCommand):
    help = 'Импортирует теги из JSON-фикстуры.'
    model = Tag
    default_fixture = '/app/data/tags.json'
