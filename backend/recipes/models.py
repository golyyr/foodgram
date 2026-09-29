from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (
    MAX_MEASUREMENT_UNIT_LENGTH,
    MAX_PRODUCT_NAME_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    MIN_COOKING_TIME,
    MIN_PRODUCT_AMOUNT,
)


class User(AbstractUser):
    """Пользователь Foodgram. Вход выполняется по email."""

    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        'Никнейм',
        max_length=150,
        unique=True,
        validators=[
            RegexValidator(
                regex=settings.USERNAME_PATTERN,
                message='Недопустимые символы в никнейме.',
            ),
        ],
    )
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.author}'


class Tag(models.Model):
    """Тег рецепта."""

    name = models.CharField(
        'Название',
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        'Идентификатор',
        max_length=MAX_TAG_SLUG_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)
        default_related_name = 'tags'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Продукт для рецептов."""

    name = models.CharField(
        'Название',
        max_length=MAX_PRODUCT_NAME_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        default_related_name = 'products'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_product',
            ),
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField('Название', max_length=MAX_RECIPE_NAME_LENGTH)
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления, мин',
        validators=[MinValueValidator(MIN_COOKING_TIME)],
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    products = models.ManyToManyField(
        Product,
        through='ProductInRecipe',
        verbose_name='Продукты',
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name


class ProductInRecipe(models.Model):
    """Количество продукта в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(MIN_PRODUCT_AMOUNT)],
    )

    class Meta:
        verbose_name = 'Продукт в рецепте'
        verbose_name_plural = 'Продукты в рецептах'
        default_related_name = 'product_amounts'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'product'),
                name='unique_recipe_product',
            ),
        ]

    def __str__(self):
        return f'{self.product.name} — {self.amount}'


class UserRecipeRelation(models.Model):
    """Абстрактная связь пользователя с рецептом."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique',
            ),
        ]

    def __str__(self):
        return f'{self.user} → {self.recipe}'


class Favorite(UserRecipeRelation):
    """Рецепт в избранном пользователя."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Рецепт в списке покупок пользователя."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
