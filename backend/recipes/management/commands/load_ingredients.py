import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает список ингредиентов из data/ingredients.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=str(Path(settings.BASE_DIR) / 'data' / 'ingredients.json'),
        )

    def handle(self, *args, **options):
        path = options['path']
        with open(path, encoding='utf-8') as file:
            data = json.load(file)

        ingredients = [
            Ingredient(
                name=item['name'],
                measurement_unit=item['measurement_unit'],
            )
            for item in data
        ]
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'Обработано {len(data)} записей. '
            f'Всего ингредиентов в базе: {Ingredient.objects.count()}.'
        ))
