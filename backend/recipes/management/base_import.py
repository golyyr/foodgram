import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class ImportJsonCommand(BaseCommand):
    """Общий импорт моделей из JSON-фикстуры."""

    model = None
    default_fixture = ''

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixture',
            default=self.default_fixture,
            help='Путь к JSON-фикстуре',
        )

    def handle(self, *args, **options):
        path = Path(options['fixture'])
        try:
            with path.open(encoding='utf-8') as json_file:
                created = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(json_file)),
                    ignore_conflicts=True,
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Данные загружены из {path.name}. '
                    f'Добавлено: {len(created)}. '
                    f'Всего записей: {self.model.objects.count()}.',
                ),
            )
        except Exception as error:
            raise CommandError(f'{path.name}: {error}') from error
