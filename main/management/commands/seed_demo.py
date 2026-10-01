import getpass
import os
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pantry.models import PantryItem
from recipes.models import Bookmark, Recipe


class Command(BaseCommand):
    help = 'Create a private demo pantry and three Figma recipe examples (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='demo')

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(username=options['username']).first()
        if not user:
            password = os.getenv('DEMO_PASSWORD') or getpass.getpass('Password akun demo baru: ')
            if len(password) < 10:
                raise CommandError('Gunakan password demo minimal 10 karakter.')
            user = User.objects.create_user(options['username'], password=password)
        today = timezone.localdate()
        for name, category, days in [('Mangga', 'Buah Segar', 2), ('Susu Sapi', 'Susu', -1), ('Yogurt Strawberry', 'Yogurt', 10)]:
            PantryItem.objects.get_or_create(owner=user, name=name, defaults={
                'category': category, 'quantity': 4, 'location': 'Kulkas',
                'stored_on': today - timedelta(days=7), 'expires_on': today + timedelta(days=days), 'is_demo': True})
        examples = [
            ('Nasi Goreng Sayur', 'Nasi dingin semalam, 1 piring\nTelur, 2 butir\nWortel, 1 buah\nBawang putih, 2 siung\nBawang merah, 3 butir\nKecap manis, 1 sdm\nGaram dan merica secukupnya\nMinyak goreng, 1 sdm',
             'Tumis bawang putih dan bawang merah sampai harum.\nMasukkan wortel, tumis sampai empuk.\nTambahkan telur dan orak-arik sampai matang.\nMasukkan nasi lalu aduk rata.\nTambahkan kecap, garam, dan merica. Masak hingga panas merata, lalu sajikan.', 2, 'recipeDesign-imgImage1.png'),
            ('Telur Dadar Wortel', 'Telur, 2 butir\nWortel, setengah buah\nDaun bawang, 1 batang\nGaram dan merica secukupnya',
             'Parut wortel dan iris daun bawang.\nKocok telur dengan sayuran dan bumbu.\nPanaskan sedikit minyak, tuang adonan.\nBalik dan masak hingga telur matang merata.', 2, 'recipeDesign-imgTelurDadarWortel.png'),
            ('Puding Roti Tawar', 'Roti tawar, 4 lembar\nTelur, 1 butir\nSusu cair, 200 ml\nGula pasir, 2 sdm\nKayu manis, seperempat sdt',
             'Potong roti dan susun di wadah tahan panas.\nCampur susu, telur, gula, dan kayu manis.\nTuang campuran ke roti.\nKukus sekitar 25 menit sampai adonan matang dan padat.', 4, 'recipeDesign-imgPudingRotiTawar.png'),
        ]
        for i, (title, ingredients, steps, portions, image) in enumerate(examples):
            recipe, created = Recipe.objects.get_or_create(author=user, title=title, defaults={
                'ingredients': ingredients, 'steps': steps, 'portions': portions, 'minutes': 15 if i < 2 else 30, 'demo_image': image})
            if created and i != 1:
                Bookmark.objects.get_or_create(user=user, recipe=recipe)
        self.stdout.write(self.style.SUCCESS(f'Data demo siap untuk {user.username}: 3 bahan + 3 resep. Password akun yang sudah ada tidak diubah.'))
