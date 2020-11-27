from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.shortcuts import reverse

from posts.models import Post, Group, Follow, Comment

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
            result_page = self.client.get(url) 
            with self.subTest('Поста нет на странице "' + url + '"'): 
                paginator = result_page.context.get('paginator')  
                if paginator is not None:  
                    result = result_page.context['page'][0]
                else:
                    result = result_page.context['post'] 
                self.assertEqual(result.text, self.post.text) 
                self.assertEqual(result.group.id,  self.group.id) 
                self.assertEqual(result.author.username, self.user.username) 

    def test_show_404(self):
        response = self.client.get('/no_existing_page/')
        self.assertEquals(response.status_code, 404)


class SprintSixTest(TestCase):
    def setUp(self):
        cache.clear()
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
        
    def test_image(self):
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
        urls = ( 
            reverse('index'), 
            reverse('profile', args=[post.author.username]),  
            reverse('post',  args=[post.author.username, post.pk]), 
            reverse('group_posts', args=[self.group.slug]), 
        )
        for url in urls: 
            with self.subTest(url=url): 
                response = self.client.get(url) 
                paginator = response.context.get('paginator')  
                if paginator is not None:  
                    post = response.context['page'][0]
                else:
                    post = response.context['post'] 
                self.assertContains(response, '<img', status_code=200)

    def test_no_image(self):
        self.client.force_login(self.user)
        small_gif= (
            b"1"
        )
        fake_img = SimpleUploadedFile(
            "small.gif",
            small_gif,
            content_type="image/gif"
        )
        response = self.client.post(
            reverse('new_post'), 
            {'text': 'post with no imag',
                'author': self.user,
                'group': self.group, 
                'image': fake_img
            }
        )
        self.assertFormError(
            response, 
            'form', 
            'image', 
            (
                'Загрузите правильное изображение. '
                'Файл, который вы загрузили, поврежден или не является'
                ' изображением.'
            )
        )
    
    def test_edit_image(self):
        cache.clear()
        self.client.force_login(self.user)
        post = Post.objects.create(
            text="Post for edit image", 
            group=self.group, 
            author=self.user
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            'small.gif', 
            small_gif,
            content_type='image/gif'
        )
        self.client.post(reverse(
            "post_edit", 
            kwargs={
                'username': self.user.username, 
                'post_id': post.id
            }),
            {
                'text': "Post after edit image",
                'image': img
            }
        )
        self.assertEqual(Post.objects.count(), 1)

        comment = Post.objects.all().first()
        self.assertNotEqual(comment.text, "Post for edit image")
        self.assertEqual(comment.text, "Post after edit image")
        self.assertEqual(comment.author, self.user)

    def test_cache(self):
        cache.clear()
        self.client.force_login(self.user)
        first_response = self.client.get(reverse('index'))
        post_cache = Post.objects.create(
            text='Post to check cache', 
            group=self.group,
            author=self.user
        )
        second_response = self.client.get(reverse('index'))
        self.assertEqual(first_response.content, second_response.content)
        key = make_template_fragment_key('index_page')
        cache.delete(key)
        third_response = self.client.get(reverse('index'))
        self.assertNotEqual(second_response.content, third_response.content)

    def test_follow(self):
        self.client.force_login(self.follower)
        self.client.post(reverse( 
            'profile_follow', 
            kwargs={'username': self.following.username} 
        ))
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.following)
        self.assertEqual(follow.user, self.follower)

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
        follow = Follow.objects.create(
            user=self.follower,
            author=self.following
        )
        post = Post.objects.create(
            text='Post for unfollow',
            author=self.following,
            group=self.group
        )
        self.assertEqual(Follow.objects.all().count(), 1)
        self.client.get(reverse( 
            'profile_unfollow', 
            kwargs={'username': self.following.username} 
        ))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_follow_index(self):
        self.client.force_login(self.follower)
        self.post = Post.objects.create(
            text='TEST_POST', 
            author=self.following
        )
        url_follow_index = reverse('follow_index')
        response = self.client.get(url_follow_index)
        self.assertEqual(response.context.get('post'), None)
        Follow.objects.create(
            user_id=self.follower.id, 
            author_id=self.following.id
        )
        response = self.client.get(url_follow_index)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)

    def test_unauth_comments(self):
        self.text = 'Test comments'
        post = Post.objects.create(
            text=self.text, 
            group=self.group,
            author=self.user
        )
        response = self.client.get(reverse(
            "add_comment", 
            kwargs={ 
                'username': self.user.username,
                'post_id': post.id 
            }), 
            {'text': 'Comment'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_auth_comments(self):
        self.text = 'Test comments'
        self.client.force_login(self.user)
        post = Post.objects.create(
            text=self.text, 
            group=self.group,
            author=self.user
        )
        self.client.post(reverse(
            "add_comment", 
            kwargs={
                'username': self.user.username,
                'post_id': post.id
            }), 
            {'text': 'Comment'}
        )
        comment = post.comments.select_related('author').first()
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, 'Comment')
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, self.user)
