from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import Recipe, Bookmark


class RecipeTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user('owner', password='testing-password-123')
        self.other = get_user_model().objects.create_user('other', password='testing-password-123')
        self.data = dict(title='Nasi Goreng', ingredients='nasi\ntelur\nwortel', steps='Tumis bahan.\nMasak nasi.', portions=2, minutes=10)
        self.recipe = Recipe.objects.create(author=self.owner, **self.data)

    def test_public_can_read_list_and_detail(self):
        for url in [reverse('recipes:index'), reverse('recipes:detail', args=[self.recipe.pk])]:
            self.assertContains(self.client.get(url), 'Nasi Goreng')
        self.assertEqual(str(self.recipe), 'Nasi Goreng')

    def test_anonymous_mutations_and_private_tabs_require_login(self):
        for name in ['add','edit','delete','bookmark']:
            args=[] if name=='add' else [self.recipe.pk]
            self.assertEqual(self.client.post(reverse('recipes:'+name,args=args), self.data).status_code,302)
        for tab in ['saved','mine']:
            self.assertEqual(self.client.get(reverse('recipes:index'), {'tab':tab}).status_code,302)

    def test_owner_crud(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('recipes:add')).status_code,200)
        self.client.post(reverse('recipes:add'),{**self.data,'title':'Sup','author':self.other.pk})
        self.assertEqual(Recipe.objects.get(title='Sup').author,self.owner)
        self.client.post(reverse('recipes:edit',args=[self.recipe.pk]),{**self.data,'title':'Nasi Baru'})
        self.recipe.refresh_from_db();self.assertEqual(self.recipe.title,'Nasi Baru')
        self.assertEqual(self.client.get(reverse('recipes:delete',args=[self.recipe.pk])).status_code,200)
        self.client.post(reverse('recipes:delete',args=[self.recipe.pk]))
        self.assertFalse(Recipe.objects.filter(pk=self.recipe.pk).exists())

    def test_other_user_cannot_edit_delete(self):
        self.client.force_login(self.other)
        for route in ['edit','delete']:
            self.assertEqual(self.client.post(reverse('recipes:'+route,args=[self.recipe.pk]),self.data).status_code,404)

    def test_bookmark_idempotence_and_privacy(self):
        self.client.force_login(self.other)
        url=reverse('recipes:bookmark',args=[self.recipe.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        for _ in range(2):
            self.assertTrue(self.client.post(url,{'saved':'1'},HTTP_X_REQUESTED_WITH='XMLHttpRequest').json()['saved'])
        self.assertEqual(Bookmark.objects.count(),1)
        self.assertContains(self.client.get(reverse('recipes:index'),{'tab':'saved'}),'Nasi Goreng')
        self.client.force_login(self.owner)
        self.assertNotContains(self.client.get(reverse('recipes:index'),{'tab':'saved'}),'Nasi Goreng')
        self.client.force_login(self.other)
        self.client.post(url,{'saved':'0'})
        self.assertEqual(Bookmark.objects.count(),0)

    def test_database_filters_match_all_selected_ingredients(self):
        for params, expected in [({'ingredient':['nasi','telur']},True),({'ingredient':['nasi','tempe']},False),({'q':'wortel'},True),({'q':'roti'},False)]:
            result=self.client.get(reverse('recipes:index'),params,HTTP_X_REQUESTED_WITH='XMLHttpRequest').json()['html']
            self.assertEqual('Nasi Goreng' in result,expected)

    def test_mine_filter(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('recipes:index'),{'tab':'mine'}),'Nasi Goreng')
        self.client.force_login(self.owner)
        self.assertContains(self.client.get(reverse('recipes:index'),{'tab':'mine'}),'Nasi Goreng')

    def test_invalid_portions_and_xss_escaping(self):
        self.client.force_login(self.owner)
        response=self.client.post(reverse('recipes:add'),{**self.data,'portions':0})
        self.assertTrue(response.context['form'].errors)
        self.recipe.title='<script>alert(1)</script>';self.recipe.save()
        response=self.client.get(reverse('recipes:index'))
        self.assertNotContains(response,'<script>alert(1)</script>')
        self.assertContains(response,'&lt;script&gt;')

    def test_csrf(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.owner)
        self.assertEqual(client.post(reverse('recipes:bookmark',args=[self.recipe.pk]),{'saved':'1'}).status_code,403)
