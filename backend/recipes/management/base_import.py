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
        try:
            path = Path(options['fixture'])
            self.model.objects.bulk_create(
                (
                    self.model(**item)
                    for item in json.load(path.open(encoding='utf-8'))
                ),
                ignore_conflicts=True,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Данные загружены из {path}. '
                    f'Всего записей: {self.model.objects.count()}.',
                ),
            )
        except Exception as error:
            raise CommandError(str(error)) from error
