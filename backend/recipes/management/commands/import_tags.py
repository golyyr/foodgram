import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Tag


class Command(BaseCommand):
    help = 'Импортирует теги из data/tags.json.'

    def handle(self, *args, **options):
        path = self._json_path()
        with path.open(encoding='utf-8') as json_file:
            payload = json.load(json_file)
        created = 0
        for item in payload:
            _, was_created = Tag.objects.get_or_create(
                slug=item['slug'].strip(),
                defaults={'name': item['name'].strip()},
            )
            created += was_created
        self.stdout.write(
            self.style.SUCCESS(
                f'Теги загружены из {path.name}. '
                f'Добавлено: {created}, всего: {Tag.objects.count()}.',
            ),
        )

    def _json_path(self):
        candidates = (
            settings.BASE_DIR / 'data' / 'tags.json',
            settings.BASE_DIR.parent / 'data' / 'tags.json',
            Path('/app/data/tags.json'),
        )
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError('Не найден файл data/tags.json')
