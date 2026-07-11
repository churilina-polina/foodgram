import django_filters as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(name__istartswith=value)


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.NumberFilter(method='filter_by_relation')
    is_in_shopping_cart = filters.NumberFilter(method='filter_by_relation')

    relation_lookups = {
        'is_favorited': 'favorites__user',
        'is_in_shopping_cart': 'shopping_cart__user',
    }

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_by_relation(self, queryset, name, value):
        user = self.request.user
        if value == 1 and user.is_authenticated:
            return queryset.filter(**{self.relation_lookups[name]: user})
        return queryset
