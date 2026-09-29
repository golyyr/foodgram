from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MIN_COOKING_TIME, MIN_PRODUCT_AMOUNT
from recipes.models import (
    Favorite,
    Product,
    ProductInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    User,
)

UNIQUE_ITEMS_ERROR = 'Элементы не должны повторяться: {items}.'


class UserSerializer(DjoserUserSerializer):
    """Пользователь в ответах API."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = [
            *DjoserUserSerializer.Meta.fields,
            'is_subscribed',
            'avatar',
        ]
        read_only_fields = fields

    def get_is_subscribed(self, author):
        request = self.context['request']
        current_user = request.user
        return (
            current_user.is_authenticated
            and current_user.subscriptions.filter(author=author).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'measurement_unit')


class ProductInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='product.id')
    name = serializers.ReadOnlyField(source='product.name')
    measurement_unit = serializers.ReadOnlyField(
        source='product.measurement_unit',
    )

    class Meta:
        model = ProductInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class ProductAmountWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    amount = serializers.IntegerField(min_value=MIN_PRODUCT_AMOUNT)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, 'recipes', 'recipes_count']
        read_only_fields = fields

    def get_recipes_count(self, author):
        return author.recipes.count()

    def get_recipes(self, author):
        request = self.context.get('request')
        recipes = author.recipes.all()
        if request is not None:
            raw_limit = request.GET.get('recipes_limit')
            try:
                recipes = recipes[:int(raw_limit)]
            except (TypeError, ValueError):
                pass
        return RecipeMinifiedSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = ProductInRecipeSerializer(
        source='product_amounts',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        return self._has_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._has_relation(recipe, ShoppingCart)

    def _has_relation(self, recipe, model):
        request = self.context['request']
        current_user = request.user
        return (
            current_user.is_authenticated
            and model.objects.filter(
                user=current_user,
                recipe=recipe,
            ).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = ProductAmountWriteSerializer(many=True, allow_empty=False)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False,
    )
    image = Base64ImageField(required=False)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        return self._validate_unique(
            ingredients,
            key=lambda item: item['id'],
        )

    def validate_tags(self, tags):
        return self._validate_unique(tags, key=lambda tag: tag)

    def validate(self, data):
        if self.instance is None and not data.get('image'):
            raise serializers.ValidationError(
                {'image': 'Картинка обязательна.'},
            )
        return data

    def _validate_unique(self, items, key):
        values = [key(item) for item in items]
        duplicates = {
            str(value) for value in values if values.count(value) > 1
        }
        if duplicates:
            raise serializers.ValidationError(
                UNIQUE_ITEMS_ERROR.format(items=sorted(duplicates)),
            )
        return items

    def create(self, validated_data):
        products = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._set_products(recipe, products)
        return recipe

    def update(self, recipe, validated_data):
        recipe.tags.set(validated_data.pop('tags'))
        recipe.product_amounts.all().delete()
        self._set_products(recipe, validated_data.pop('ingredients'))
        return super().update(recipe, validated_data)

    def _set_products(self, recipe, products):
        ProductInRecipe.objects.bulk_create(
            ProductInRecipe(
                recipe=recipe,
                product=item['id'],
                amount=item['amount'],
            )
            for item in products
        )

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data
