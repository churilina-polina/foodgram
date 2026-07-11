from django.db.models import Sum

from recipes.models import Recipe, RecipeIngredient


def build_shopping_cart_content(user):
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__shopping_cart__user=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes = Recipe.objects.filter(
        shopping_cart__user=user,
    ).order_by('name')

    lines = ['Список покупок', '']
    lines += [
        f"{index}. {item['ingredient__name'].capitalize()} "
        f"({item['ingredient__measurement_unit']}) — "
        f"{item['total_amount']}"
        for index, item in enumerate(ingredients, start=1)
    ]
    lines += ['', 'Рецепты в списке покупок:']
    lines += [f'- {recipe.name}' for recipe in recipes]
    return '\n'.join(lines)
