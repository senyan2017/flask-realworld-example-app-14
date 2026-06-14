# coding: utf-8

from flask import url_for
from datetime import datetime

class TestArticleViews:

    def test_get_articles_by_author(self, testapp, user):
        user = user.get()
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})

        token = str(resp.json['user']['token'])
        for _ in range(2):
            testapp.post_json(url_for('articles.make_article'), {
                "article": {
                    "title": "How to train your dragon {}".format(_),
                    "description": "Ever wonder how?",
                    "body": "You have to believe",
                    "tagList": ["reactjs", "angularjs", "dragons"]
                }
            }, headers={
                'Authorization': 'Token {}'.format(token)
            })

        resp = testapp.get(url_for('articles.get_articles', author=user.username))
        assert len(resp.json['articles']) == 2

    def test_favorite_an_article(self, testapp, user):
        user = user.get()
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})

        token = str(resp.json['user']['token'])
        resp1 = testapp.post_json(url_for('articles.make_article'), {
            "article": {
                "title": "How to train your dragon",
                "description": "Ever wonder how?",
                "body": "You have to believe",
                "tagList": ["reactjs", "angularjs", "dragons"]
            }
        }, headers={
            'Authorization': 'Token {}'.format(token)
        })

        resp = testapp.post(url_for('articles.favorite_an_article',
                                    slug=resp1.json['article']['slug']),
                            headers={
                                'Authorization': 'Token {}'.format(token)
                                }
                           )
        assert resp.json['article']['favorited']

    def test_get_articles_by_favoriter(self, testapp, user):
        user = user.get()
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})

        token = str(resp.json['user']['token'])
        for _ in range(2):
            testapp.post_json(url_for('articles.make_article'), {
                "article": {
                    "title": "How to train your dragon {}".format(_),
                    "description": "Ever wonder how?",
                    "body": "You have to believe",
                    "tagList": ["reactjs", "angularjs", "dragons"]
                }
            }, headers={
                'Authorization': 'Token {}'.format(token)
            })

        resp = testapp.get(url_for('articles.get_articles', author=user.username))
        assert len(resp.json['articles']) == 2

    def test_make_article(self, testapp, user):
        user = user.get()
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})

        token = str(resp.json['user']['token'])
        resp = testapp.post_json(url_for('articles.make_article'), {
            "article": {
                "title": "How to train your dragon",
                "description": "Ever wonder how?",
                "body": "You have to believe",
                "tagList": ["reactjs", "angularjs", "dragons"]
            }
        }, headers={
            'Authorization': 'Token {}'.format(token)
        })
        assert resp.json['article']['author']['email'] == user.email
        assert resp.json['article']['body'] == 'You have to believe'

    def test_make_comment_correct_schema(self, testapp, user):
        from conduit.profile.serializers import profile_schema
        user = user.get()
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})

        token = str(resp.json['user']['token'])
        resp = testapp.post_json(url_for('articles.make_article'), {
            "article": {
                "title": "How to train your dragon",
                "description": "Ever wonder how?",
                "body": "You have to believe",
                "tagList": ["reactjs", "angularjs", "dragons"]
            }
        }, headers={
            'Authorization': 'Token {}'.format(token)
        })
        slug = resp.json['article']['slug']
        # make a comment
        resp = testapp.post_json(url_for('articles.make_comment_on_article', slug=slug), {
            "comment": {
                "createdAt": datetime.now().isoformat(),
                "body": "You have to believe",
            }
        }, headers={
            'Authorization': 'Token {}'.format(token)
        })

        # check
        authorp = resp.json['comment']['author']
        del authorp['following']
        # assert profile_schema.dump(user).data['profile'] == authorp
        assert profile_schema.dump(user)['profile'] == authorp

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _login(self, testapp, user):
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': user.email,
            'password': 'myprecious'
        }})
        return str(resp.json['user']['token'])

    def _auth(self, token):
        return {'Authorization': 'Token {}'.format(token)}

    def _create_article(self, testapp, token, title, tags=None):
        return testapp.post_json(url_for('articles.make_article'), {
            "article": {
                "title": title,
                "description": "Ever wonder how?",
                "body": "You have to believe",
                "tagList": tags or [],
            }
        }, headers=self._auth(token))

    # ------------------------------------------------------------------
    # pagination total count
    # ------------------------------------------------------------------
    def test_articles_count_reflects_total_not_page(self, testapp, user):
        """articlesCount must be the total, even when a page is limited."""
        user = user.get()
        token = self._login(testapp, user)
        for i in range(3):
            self._create_article(testapp, token, "Dragon {}".format(i))

        resp = testapp.get(url_for('articles.get_articles', limit=2))
        assert len(resp.json['articles']) == 2
        assert resp.json['articlesCount'] == 3

    def test_articles_count_with_offset(self, testapp, user):
        """offset trims the page but the total stays put."""
        user = user.get()
        token = self._login(testapp, user)
        for i in range(3):
            self._create_article(testapp, token, "Offset dragon {}".format(i))

        resp = testapp.get(url_for('articles.get_articles', limit=2, offset=2))
        assert len(resp.json['articles']) == 1
        assert resp.json['articlesCount'] == 3

    def test_articles_count_with_tag_filter(self, testapp, user):
        """Filtered total must match the filter, not the unfiltered table."""
        user = user.get()
        token = self._login(testapp, user)
        self._create_article(testapp, token, "React one", tags=["reactjs"])
        self._create_article(testapp, token, "React two", tags=["reactjs"])
        self._create_article(testapp, token, "Vue one", tags=["vuejs"])

        # page smaller than the filtered total
        resp = testapp.get(url_for('articles.get_articles', tag="reactjs", limit=1))
        assert len(resp.json['articles']) == 1
        assert resp.json['articlesCount'] == 2

        resp = testapp.get(url_for('articles.get_articles', tag="vuejs"))
        assert len(resp.json['articles']) == 1
        assert resp.json['articlesCount'] == 1

    def test_articles_count_with_author_filter(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)
        for i in range(2):
            self._create_article(testapp, token, "Author dragon {}".format(i))

        resp = testapp.get(url_for('articles.get_articles',
                                   author=user.username, limit=1))
        assert len(resp.json['articles']) == 1
        assert resp.json['articlesCount'] == 2

    def test_articles_empty_result_count_is_zero(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)
        self._create_article(testapp, token, "Lonely dragon")

        resp = testapp.get(url_for('articles.get_articles', author="nobody-here"))
        assert resp.json['articles'] == []
        assert resp.json['articlesCount'] == 0

    # ------------------------------------------------------------------
    # deleting missing objects
    # ------------------------------------------------------------------
    def test_delete_article_success(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)
        resp = self._create_article(testapp, token, "Doomed dragon")
        slug = resp.json['article']['slug']

        resp = testapp.delete(url_for('articles.delete_article', slug=slug),
                              headers=self._auth(token))
        assert resp.status_code == 200

        resp = testapp.get(url_for('articles.get_articles'))
        assert resp.json['articlesCount'] == 0

    def test_delete_nonexistent_article_returns_404(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)

        resp = testapp.delete(url_for('articles.delete_article', slug="ghost-slug"),
                              headers=self._auth(token), expect_errors=True)
        assert resp.status_code == 404
        assert resp.json['errors']['body'] == ['Article not found']

    def test_delete_nonexistent_comment_returns_404(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)
        resp = self._create_article(testapp, token, "Commented dragon")
        slug = resp.json['article']['slug']

        resp = testapp.delete(
            url_for('articles.delete_comment_on_article', slug=slug, cid=999999),
            headers=self._auth(token), expect_errors=True)
        assert resp.status_code == 404
        assert resp.json['errors']['body'] == ['Comment not found']

    def test_delete_comment_on_missing_article_returns_404(self, testapp, user):
        user = user.get()
        token = self._login(testapp, user)

        resp = testapp.delete(
            url_for('articles.delete_comment_on_article', slug="ghost-slug", cid=1),
            headers=self._auth(token), expect_errors=True)
        assert resp.status_code == 404
        assert resp.json['errors']['body'] == ['Article not found']

    def test_delete_others_comment_returns_422(self, testapp, user):
        """Deleting a comment you don't own is a clear 422, not a silent success."""
        author = user.get()
        author_token = self._login(testapp, author)
        resp = self._create_article(testapp, author_token, "Owned dragon")
        slug = resp.json['article']['slug']
        cresp = testapp.post_json(
            url_for('articles.make_comment_on_article', slug=slug),
            {"comment": {"createdAt": datetime.now().isoformat(), "body": "mine"}},
            headers=self._auth(author_token))
        cid = cresp.json['comment']['id']

        intruder = user.get()
        intruder_token = self._login(testapp, intruder)
        resp = testapp.delete(
            url_for('articles.delete_comment_on_article', slug=slug, cid=cid),
            headers=self._auth(intruder_token), expect_errors=True)
        assert resp.status_code == 422
        assert resp.json['errors']['body'] == ['Not your comment']
