from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.shortcuts import reverse
from django.core.cache.utils import make_template_fragment_key

from posts.models import Post, Group, Follow

User = get_user_model()


class PostsTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@test.ru',
            password='12345'
        )
        self.group = Group.objects.create(
            title='testers',
            slug='testers',
            description='test_group'
        )

    def test_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse(
            'profile', 
            args=[self.user.username]
        ))
        self.assertEqual(response.status_code, 200)

    def test_authorized_user_newpost_page(self):
        response = self.client.get(reverse('new_post'), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpost_page(self):
        response = self.client.get(reverse('new_post')) 
        self.assertRedirects( 
            response,  
            f"{reverse('login')}?next={reverse('new_post')}",  
            status_code=302,  
            target_status_code=200 
        ) 

    def test_new_post(self):
        self.client.force_login(self.user)
        current_posts_count = Post.objects.count()
        data = {'text': 'New test post', 'group': self.group.id}
        response = self.client.post(
            reverse('new_post'),
            data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), current_posts_count + 1) 
        paginator = response.context.get('paginator') 
        if paginator is not None:  
            result = response.context['page'][0]
        else:
            result = response.context['post'] 
        self.assertEqual(result.text, data['text'])
        self.assertEqual(result.author.username, self.user.username)
        self.assertEqual(result.group, self.group) 

    def test_edit_post(self):
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            text='Test post', 
            author=self.user,
            group= self.group
        )
        self.edit_group = Group.objects.create(
            title='Sec. testers',
            slug='Sec. testers',
            description='test_group_num_2'
        )
        first_posts_count = Post.objects.count()
        edit_text = 'Test post after edit'
        data = {'text': edit_text, 
            'group': self.edit_group.id,
        }
        response_edit_post = self.client.post(
            reverse(
                'post_edit', 
                args=[self.user.username, self.post.id]), 
            data
        ) 
        second_posts_count = Post.objects.count()
        self.assertEqual(first_posts_count, second_posts_count, 
            'Страница редактировани поста создает еще одну страницу')
        self.assertEqual(response_edit_post.status_code, 302) 
        self.post_text = Post.objects.get(id=self.post.id).text
        self.assertEqual(self.post_text, edit_text)
        self.post_group = Post.objects.get(id=self.post.id).group
        self.assertEqual(self.post_group, self.edit_group)
       
    def test_show_post(self): 
        self.client.force_login(self.user)
        self.post = Post.objects.create(
            text='Test post', 
            author=self.user,
            group= self.group
        )
        urls = ( 
            reverse('index'), 
            reverse('profile', args=[self.user.username]),  
            reverse('post',  args=[self.user.username, self.post.id]), 
            reverse('group_posts', args=[self.group.slug]), 
        ) 
        for url in urls: 
            cache.clear() 
            res_page = self.client.get(url) 
            with self.subTest('Поста нет на странице "' + url + '"'): 
                paginator = res_page.context.get('paginator')  
                if paginator is not None:  
                    result = res_page.context['page'][0]
                else:
                    result = res_page.context['post'] 
                self.assertEqual(result.text, self.post.text) 
                self.assertEqual(result.group.id,  self.group.id) 
                self.assertEqual(result.author.username, self.user.username) 

    def test_show_404(self):
        response = self.client.get('/no_existing_page/')
        self.assertEquals(response.status_code, 404)


class SPRINT6_Test(TestCase):
    def setUp(self):
        #cache.clear()
        self.client = Client()
        self.user = User.objects.create_user(
            username='test_user',
            email='test_user@test.ru',
            password='12345'
        )
        self.follower = User.objects.create_user(
            username='testfollower',
            email='testfollower@test.ru',
            password='testpass1'
        )
        self.following = User.objects.create_user(
            username='testfollowing',
            email='testfollowing@test.ru',
            password='testpass2'
        )
        self.group = Group.objects.create(
            title='test',
            slug='test',
            description='test_group'
        )
        self.post = Post.objects.create(
            text='TEST_POST', 
            author=self.following
        )
        self.key = make_template_fragment_key('index_page')
        
    def test_post_view_image(self):
        self.client.force_login(self.user)
        small_gif= (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            "small.gif",
            small_gif,
            content_type="image/gif"
        )
        post = Post.objects.create(
            text='Test post with img', 
            author=self.user,
            group= self.group,
            image= img
        )
        response=self.client.post(reverse(
            'post', 
             kwargs={
                    'username': post.author,
                    'post_id': post.id,}
        ))
        self.assertContains(response, '<img', status_code=200)

    def test_profile_image(self):
        self.client.force_login(self.user)
        small_gif= (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        img = SimpleUploadedFile(
            "small.gif",
            small_gif,
            content_type="image/gif"
        )
        post = Post.objects.create(
            text='Test post with img', 
            author=self.user,
            group= self.group,
            image= img
        )
        response = self.client.post(reverse(
            'profile', 
            kwargs={'username': post.author}
        ))
        self.assertContains(response, '<img')


    def test_cache(self):
        cache.clear()
        self.client.force_login(self.user)
        first_response=self.client.get(reverse('index'))
        group = Group.objects.create(
            title='testers',
            slug='testers',
            description='test_group'
        )
        group.save()
        post = Post.objects.create(
            text='Test post', 
            author=self.user,
            group= self.group
        )
        second_response=self.client.get(reverse('index'))
        self.assertEqual(first_response.context, second_response.context)
        cache.touch(self.key, 0)
        third_response=self.client.get(reverse('index'))
        self.assertNotEqual(second_response.context, third_response.context)

    def test_follow(self):
        self.client.force_login(self.follower)
        url_profile = reverse(
            'profile',
            kwargs={'username': self.following.username}
        )
        response_profile = self.client.get(url_profile)
        self.assertContains(response_profile, 'Подписаться')

    def test_double_follow(self):
        self.client.force_login(self.follower)
        url_profile_follow = reverse(
            'profile_follow',
            kwargs={'username': self.following.username}
        )
        self.client.get(url_profile_follow, follow=True)
        self.assertEqual(Follow.objects.all().count(), 1)
        self.client.get(url_profile_follow, follow=True)
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_self_follow(self):
        self.client.force_login(self.follower)
        url_profile_follow = reverse(
            'profile_follow',
            kwargs={'username': self.follower.username}
        )
        self.assertEqual(Follow.objects.all().count(), 0)
        self.client.get(url_profile_follow, follow=True)
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        self.client.force_login(self.follower)
        Follow.objects.create(user_id=self.follower.id, author_id=self.following.id)
        self.assertEqual(Follow.objects.all().count(), 1)
        url_profile = reverse(
            'profile',
            kwargs={'username': self.following.username}
        )
        response_profile = self.client.get(url_profile, follow=True)
        self.assertContains(response_profile, 'Отписаться')

    def test_follow_index(self):
        self.client.force_login(self.follower)
        url_follow_index = reverse('follow_index')
        response_profile = self.client.get(url_follow_index)
        self.assertNotContains(response_profile, 'TEST_POST')

        Follow.objects.create(user_id=self.follower.id, author_id=self.following.id)

        response_profile = self.client.get(url_follow_index)
        self.assertContains(response_profile, 'TEST_POST')

    def test_comments(self):

        self.text = 'Test comments'
        self.post = Post.objects.create(
            text='Test post', 
            author=self.following
        )
        response = self.client.post(
            reverse(
                'add_comment', 
                args=[self.following.username, self.post.id]), 
            {'text': 'Error text'}
        )
        self.assertRedirects(
            response, 
            f'/auth/login/?next=/{self.following}/{self.post.pk}/comment/', 
            status_code=302
        )
        self.client.force_login(self.follower)
        response = self.client.post(
            reverse(
                'add_comment', 
                args=[self.following.username, self.post.id]
            ), 
            {'text': self.text}
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse(
                'post', 
                args=[self.following.username, self.post.id]
            )
        )
        self.assertContains(response, self.text, status_code=200, html=False,)
