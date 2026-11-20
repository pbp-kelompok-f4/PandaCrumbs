from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from pantry.models import PantryItem
from recipes.models import Bookmark, Recipe


class CP1APITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user('owner', password='test-pass')
        cls.other = get_user_model().objects.create_user('other', password='test-pass')
        cls.items = [PantryItem.objects.create(
            owner=user, name='Rice', category='Bahan Pokok', quantity=2,
            location='Rak Dapur', expires_on=timezone.localdate(),
        ) for user in (cls.owner, cls.other)]
        cls.recipe = Recipe.objects.create(author=cls.owner, title='Rice and egg',
            ingredients='rice\negg', steps='Cook\nServe', minutes=15,
            demo_image='recipeDesign-imgImage1.png')
        cls.other_recipe = Recipe.objects.create(author=cls.other, title='Slow soup',
            ingredients='carrot', steps='Boil', minutes=30)
        Bookmark.objects.create(user=cls.other, recipe=cls.recipe)

    def test_pantry_requires_login_and_isolates_owners(self):
        url = '/api/pantry/'
        for path in (url, f'{url}{self.items[0].pk}/'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTrue(self.client.login(username='owner', password='test-pass'))
        response = self.client.get(url, {'owner': self.other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r['id'] for r in response.json()], [self.items[0].pk])
        self.assertEqual(self.client.get(f'{url}{self.items[1].pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'{url}999999/').status_code, 404)
        self.client.force_login(self.other)
        self.assertEqual([r['id'] for r in self.client.get(url).json()], [self.items[1].pk])

    def test_pantry_expiry_boundaries_come_from_model(self):
        self.client.force_login(self.owner)
        item = self.items[0]
        for days, expected in ((-1, 'expired'), (0, 'soon'), (3, 'soon'), (4, 'safe')):
            item.expires_on = timezone.localdate() + timedelta(days=days)
            item.save()
            response = self.client.get(f'/api/pantry/{item.pk}/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['status'], expected)
            self.assertEqual(response.json()['quantity'], 2)

    def test_recipes_are_public_with_useful_fields_and_no_private_user_data(self):
        response = self.client.get('/api/recipes/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        response = self.client.get(f'/api/recipes/{self.recipe.pk}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['ingredients'], 'rice\negg')
        self.assertEqual(data['steps'], 'Cook\nServe')
        self.assertEqual(data['author_name'], 'owner')
        self.assertTrue(data['image_url'].endswith('/static/main/images/recipeDesign-imgImage1.png'))
        self.assertFalse(data['is_saved'])
        self.recipe.image_url = 'https://example.com/recipe.png'
        self.recipe.save()
        self.assertEqual(self.client.get(f'/api/recipes/{self.recipe.pk}/').json()['image_url'],
                         'https://example.com/recipe.png')
        self.assertEqual(self.client.get(f'/api/recipes/{self.other_recipe.pk}/').json()['image_url'], '')
        for field in ('email', 'password', 'bookmarks'):
            self.assertNotIn(field, data)
        self.assertEqual(self.client.get('/api/recipes/999999/').status_code, 404)

    def test_private_recipe_tabs_and_bookmark_status_do_not_leak(self):
        for tab in ('mine', 'saved'):
            self.assertEqual(self.client.get('/api/recipes/', {'tab': tab}).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get('/api/recipes/', {'tab': 'saved'}).json(), [])
        self.assertEqual([r['id'] for r in self.client.get('/api/recipes/', {'tab': 'mine'}).json()], [self.recipe.pk])
        self.client.force_login(self.other)
        data = self.client.get('/api/recipes/', {'tab': 'saved', 'user': self.owner.pk}).json()
        self.assertEqual([r['id'] for r in data], [self.recipe.pk])
        self.assertTrue(data[0]['is_saved'])
        self.assertEqual(self.client.get(f'/api/recipes/{self.recipe.pk}/', {'tab': 'mine'}).status_code, 404)

    def test_recipe_filters_combine_and_quick_excludes_thirty_minutes(self):
        for query, ids in (({'q': 'rice', 'ingredient': ['rice', 'egg'], 'quick': '1'}, [self.recipe.pk]),
                           ({'ingredient': ['rice', 'carrot']}, []),
                           ({'quick': '1'}, [self.recipe.pk]),
                           ({'tab': 'unknown'}, [self.recipe.pk, self.other_recipe.pk])):
            response = self.client.get('/api/recipes/', query)
            self.assertEqual(response.status_code, 200)
            self.assertEqual([r['id'] for r in response.json()], ids)

    def test_writes_are_rejected_and_existing_data_preserved(self):
        self.client.force_login(self.owner)
        for url, obj in (('/api/pantry/', self.items[0]), ('/api/recipes/', self.recipe)):
            for method, path in (('post', url), ('put', f'{url}{obj.pk}/'),
                                 ('patch', f'{url}{obj.pk}/'), ('delete', f'{url}{obj.pk}/')):
                with self.subTest(method=method, path=path):
                    response = getattr(self.client, method)(path, '{}', content_type='application/json')
                    self.assertEqual(response.status_code, 405)
            self.assertTrue(type(obj).objects.filter(pk=obj.pk).exists())
        self.items[0].refresh_from_db()
        self.assertEqual(self.items[0].quantity, 2)

    def test_empty_pantry_is_an_array(self):
        self.client.force_login(get_user_model().objects.create_user('empty'))
        response = self.client.get('/api/pantry/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_modules_three_to_five_api_routes_are_removed(self):
        self.client.force_login(self.owner)
        for path in ('waste-audit', 'community/offers', 'habit-challenge/plans', 'habit-challenge/completions'):
            self.assertEqual(self.client.get(f'/api/{path}/').status_code, 404)
