import csv
import uuid
from datetime import timedelta
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image

from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from users.models import User

TEST_PASSWORD = 'Testpass123'
ADMIN_EMAIL = 'admin@foodgram.ru'
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'Adminpass123'

TAGS = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
)

USERS = (
    {
        'email': 'vasya@foodgram.ru',
        'username': 'vasya',
        'first_name': 'Вася',
        'last_name': 'Иванов',
    },
    {
        'email': 'masha@foodgram.ru',
        'username': 'masha',
        'first_name': 'Маша',
        'last_name': 'Петрова',
    },
    {
        'email': 'petya@foodgram.ru',
        'username': 'petya',
        'first_name': 'Петя',
        'last_name': 'Сидоров',
    },
)

RECIPES = (
    {
        'author': ADMIN_EMAIL,
        'name': 'Яичница',
        'text': 'Обжарьте яйца на сковороде и посолите.',
        'cooking_time': 10,
        'tags': ('breakfast',),
        'color': (240, 200, 80),
        'days_ago': 1,
        'ingredients': (
            ('яйца куриные', 'г', 120),
            ('соль', 'г', 2),
        ),
    },
    {
        'author': 'vasya@foodgram.ru',
        'name': 'Блины',
        'text': (
            'Смешайте молоко, яйца, муку, сахар и соль. '
            'Жарьте тонкие блины на разогретой сковороде.'
        ),
        'cooking_time': 30,
        'tags': ('breakfast',),
        'color': (244, 196, 96),
        'days_ago': 12,
        'ingredients': (
            ('мука', 'г', 200),
            ('молоко', 'мл', 400),
            ('яйца куриные', 'г', 120),
            ('сахар', 'г', 30),
            ('соль', 'г', 3),
        ),
    },
    {
        'author': 'masha@foodgram.ru',
        'name': 'Омлет с молоком',
        'text': 'Взбейте яйца с молоком и солью, обжарьте на сковороде.',
        'cooking_time': 15,
        'tags': ('breakfast',),
        'color': (245, 222, 120),
        'days_ago': 11,
        'ingredients': (
            ('яйца куриные', 'г', 150),
            ('молоко', 'мл', 80),
            ('соль', 'г', 2),
        ),
    },
    {
        'author': 'petya@foodgram.ru',
        'name': 'Овсяная каша',
        'text': 'Сварите хлопья на молоке, добавьте сахар и щепотку соли.',
        'cooking_time': 20,
        'tags': ('breakfast',),
        'color': (214, 176, 120),
        'days_ago': 10,
        'ingredients': (
            ('молоко', 'мл', 250),
            ('сахар', 'г', 15),
            ('соль', 'г', 1),
        ),
    },
    {
        'author': 'vasya@foodgram.ru',
        'name': 'Картофельное пюре',
        'text': 'Отварите картофель, разомните с молоком и солью.',
        'cooking_time': 40,
        'tags': ('lunch',),
        'color': (232, 214, 160),
        'days_ago': 8,
        'ingredients': (
            ('картофель', 'г', 500),
            ('молоко', 'мл', 100),
            ('соль', 'г', 5),
        ),
    },
    {
        'author': 'masha@foodgram.ru',
        'name': 'Салат из авокадо',
        'text': 'Нарежьте авокадо и лук, посолите и сразу подавайте.',
        'cooking_time': 10,
        'tags': ('lunch',),
        'color': (120, 176, 96),
        'days_ago': 6,
        'ingredients': (
            ('авокадо', 'г', 200),
            ('лук репчатый', 'г', 40),
            ('соль', 'г', 2),
        ),
    },
    {
        'author': 'petya@foodgram.ru',
        'name': 'Суп с картофелем',
        'text': 'Сварите картофель с луком, посолите в конце варки.',
        'cooking_time': 45,
        'tags': ('lunch',),
        'color': (196, 140, 72),
        'days_ago': 5,
        'ingredients': (
            ('картофель', 'г', 400),
            ('лук репчатый', 'г', 80),
            ('соль', 'г', 6),
        ),
    },
    {
        'author': 'vasya@foodgram.ru',
        'name': 'Жареный картофель',
        'text': 'Обжарьте картофель с луком до золотистой корочки.',
        'cooking_time': 35,
        'tags': ('dinner',),
        'color': (210, 150, 70),
        'days_ago': 3,
        'ingredients': (
            ('картофель', 'г', 450),
            ('лук репчатый', 'г', 70),
            ('соль', 'г', 4),
        ),
    },
    {
        'author': 'masha@foodgram.ru',
        'name': 'Абрикосовый десерт',
        'text': 'Смешайте абрикосы с сахаром и подайте охлаждёнными.',
        'cooking_time': 15,
        'tags': ('dinner',),
        'color': (232, 128, 72),
        'days_ago': 2,
        'ingredients': (
            ('абрикосы', 'г', 300),
            ('сахар', 'г', 40),
        ),
    },
    {
        'author': 'petya@foodgram.ru',
        'name': 'Сладкие блины',
        'text': 'Приготовьте блины и подайте с сахаром.',
        'cooking_time': 25,
        'tags': ('dinner', 'breakfast'),
        'color': (220, 160, 80),
        'days_ago': 0,
        'ingredients': (
            ('мука', 'г', 180),
            ('молоко', 'мл', 300),
            ('яйца куриные', 'г', 100),
            ('сахар', 'г', 25),
        ),
    },
)


class Command(BaseCommand):
    help = 'Загружает ингредиенты, теги, тестовых пользователей и рецепты.'

    def handle(self, *args, **options):
        with transaction.atomic():
            self._load_ingredients()
            self._load_tags()
            self._load_users()
            self._load_recipes()
        self.stdout.write(self.style.SUCCESS('Начальные данные готовы.'))

    def _csv_path(self):
        candidates = (
            settings.BASE_DIR / 'data' / 'ingredients.csv',
            settings.BASE_DIR.parent / 'data' / 'ingredients.csv',
            Path('/app/data/ingredients.csv'),
        )
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError('Не найден файл data/ingredients.csv')

    def _load_ingredients(self):
        if Ingredient.objects.exists():
            self.stdout.write('Ингредиенты уже загружены.')
            return
        batch = []
        with self._csv_path().open(encoding='utf-8') as csv_file:
            for row in csv.reader(csv_file):
                if len(row) < 2:
                    continue
                name = row[0].strip()
                unit = row[1].strip()
                if name and unit:
                    batch.append(
                        Ingredient(name=name, measurement_unit=unit),
                    )
        Ingredient.objects.bulk_create(batch, batch_size=500)
        self.stdout.write(f'Ингредиентов: {len(batch)}')

    def _load_tags(self):
        for name, slug in TAGS:
            Tag.objects.get_or_create(slug=slug, defaults={'name': name})

    def _load_users(self):
        if not User.objects.filter(email=ADMIN_EMAIL).exists():
            User.objects.create_superuser(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                first_name='Админ',
                last_name='Фудграм',
                password=ADMIN_PASSWORD,
            )
        for item in USERS:
            if User.objects.filter(email=item['email']).exists():
                continue
            User.objects.create_user(password=TEST_PASSWORD, **item)

    def _load_recipes(self):
        for item in RECIPES:
            author = User.objects.get(email=item['author'])
            recipe_exists = Recipe.objects.filter(
                author=author,
                name=item['name'],
            ).exists()
            if recipe_exists:
                continue
            recipe = Recipe.objects.create(
                author=author,
                name=item['name'],
                text=item['text'],
                cooking_time=item['cooking_time'],
                image=self._image(item['color']),
            )
            recipe.tags.set(Tag.objects.filter(slug__in=item['tags']))
            IngredientInRecipe.objects.bulk_create([
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(
                        name=name,
                        measurement_unit=unit,
                    ),
                    amount=amount,
                )
                for name, unit, amount in item['ingredients']
            ])
            published = timezone.now() - timedelta(days=item['days_ago'])
            Recipe.objects.filter(pk=recipe.pk).update(pub_date=published)

    def _image(self, color):
        image = Image.new('RGB', (640, 420), color)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return ContentFile(buffer.getvalue(), name=f'{uuid.uuid4().hex}.png')
