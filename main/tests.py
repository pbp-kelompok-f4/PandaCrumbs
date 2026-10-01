from io import StringIO
from unittest.mock import Mock, patch
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from pantry.models import PantryItem
from recipes.models import Recipe


class AccountTests(TestCase):
    def test_landing_and_login_pages(self):
        for url in ['/', '/accounts/login/', '/accounts/register/']:
            self.assertEqual(self.client.get(url).status_code,200)

    def test_registration_and_password_validation(self):
        data={'username':'newuser','email':'test@example.com','password1':'short','password2':'short'}
        response=self.client.post(reverse('main:register'),data)
        self.assertTrue(response.context['form'].errors)
        data.update(password1='long-test-secret-135!',password2='long-test-secret-135!')
        self.assertEqual(self.client.post(reverse('main:register'),data).status_code,302)
        self.assertEqual(self.client.get('/pantry/').status_code,200)
        self.assertEqual(self.client.get(reverse('main:register')).status_code,302)
        self.assertEqual(self.client.get('/accounts/logout/').status_code,405)
        self.client.post('/accounts/logout/')
        self.assertEqual(self.client.get('/pantry/').status_code,302)

    def test_login_rejects_external_redirect(self):
        get_user_model().objects.create_user('user',password='long-test-secret-135!')
        response=self.client.post('/accounts/login/',{'username':'user','password':'long-test-secret-135!','next':'https://example.com/'})
        self.assertEqual(response.url,'/pantry/')

    def test_seed_is_idempotent_and_keeps_password(self):
        user=get_user_model().objects.create_user('demo',password='original-password')
        call_command('seed_demo',stdout=StringIO());call_command('seed_demo',stdout=StringIO())
        self.assertEqual(PantryItem.objects.count(),3);self.assertEqual(Recipe.objects.count(),3)
        user.refresh_from_db();self.assertTrue(user.check_password('original-password'))


class ProductSearchTests(TestCase):
    def setUp(self):
        cache.clear()
        user=get_user_model().objects.create_user('searcher',password='long-test-secret')
        self.client.force_login(user)
        self.url=reverse('main:products')

    def tearDown(self):
        cache.clear()

    def test_auth_and_min_length(self):
        self.assertEqual(self.client.get(self.url,{'q':'a'}).status_code,400)
        self.client.logout();self.assertEqual(self.client.get(self.url,{'q':'milk'}).status_code,302)

    @patch('main.views.requests.get')
    def test_search_cache_category_and_throttle(self,get):
        get.return_value=Mock(json=lambda:{'products':[{'product_name':'Milk','code':'123','categories':'Dairy'}]})
        params={'q':'milk','category':'dairy'}
        for _ in range(2):
            response=self.client.get(self.url,params)
            self.assertEqual(response.json()['products'][0]['name'],'Milk')
        self.assertEqual(get.call_count,1)
        self.assertEqual(get.call_args.kwargs['params']['tag_0'],'dairy')
        self.assertEqual(self.client.get(self.url,{'q':'bread'}).status_code,429)

    @patch('main.views.requests.get',side_effect=requests.Timeout)
    def test_api_timeout_returns_actionable_error(self,get):
        response=self.client.get(self.url,{'q':'milk'})
        self.assertEqual(response.status_code,503)
        self.assertIn('manual',response.json()['error'])

    @patch('main.views.requests.get')
    def test_invalid_upstream_payload(self,get):
        get.return_value=Mock(json=lambda:{'products':None})
        self.assertEqual(self.client.get(self.url,{'q':'milk'}).status_code,503)
