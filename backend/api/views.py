from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Product,
    ProductInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

from .filters import ProductFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    ProductSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from .shopping_list import render_shopping_list


class UserViewSet(DjoserUserViewSet):
    pagination_class = LimitPagination
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        if request.method == 'DELETE':
            User.objects.filter(pk=request.user.pk).update(avatar='')
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                self.paginate_queryset(
                    User.objects.filter(
                        author_subscriptions__user=request.user,
                    ),
                ),
                many=True,
                context={'request': request},
            ).data,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=request.user,
                author_id=id,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = self.get_object()
        if request.user == author:
            raise ValidationError(
                {'errors': 'Нельзя подписаться на самого себя.'},
            )
        _, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            raise ValidationError({
                'errors': (
                    f'Вы уже подписаны на пользователя {author.username}.'
                ),
            })
        return Response(
            UserWithRecipesSerializer(
                author,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
    filterset_class = ProductFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        recipes = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'product_amounts__product',
        )
        current_user = self.request.user
        if current_user.is_authenticated:
            recipes = recipes.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=current_user,
                        recipe=OuterRef('pk'),
                    ),
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=current_user,
                        recipe=OuterRef('pk'),
                    ),
                ),
            )
        return recipes

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update', 'update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise ValidationError({
                'errors': f'Рецепт с id={pk} не найден.',
            })
        return Response({
            'short-link': request.build_absolute_uri(
                reverse('short-link', args=[pk]),
            ),
        })

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        return self._toggle_relation(request, Favorite)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(request, ShoppingCart)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        recipes = Recipe.objects.filter(
            shoppingcarts__user=request.user,
        ).select_related('author').prefetch_related('tags')
        return FileResponse(
            render_shopping_list(
                ProductInRecipe.objects.filter(
                    recipe__shoppingcarts__user=request.user,
                ).values(
                    'product__name',
                    'product__measurement_unit',
                ).annotate(
                    total=Sum('amount'),
                ).order_by('product__name'),
                recipes,
            ),
            as_attachment=True,
            filename='shopping-list.txt',
            content_type='text/plain',
        )

    def _toggle_relation(self, request, model):
        if request.method == 'DELETE':
            get_object_or_404(
                model,
                user=request.user,
                recipe_id=self.kwargs['pk'],
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        recipe = self.get_object()
        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            raise ValidationError({
                'errors': (
                    f'Рецепт «{recipe.name}» уже добавлен '
                    f'в {model._meta.verbose_name}.'
                ),
            })
        return Response(
            RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
