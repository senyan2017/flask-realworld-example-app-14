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

    # -- helpers for the related-articles tests -------------------------------

    def _login_token(self, testapp, muser):
        resp = testapp.post_json(url_for('user.login_user'), {'user': {
            'email': muser.email,
            'password': 'myprecious'
        }})
        return str(resp.json['user']['token'])

    def _make_article(self, testapp, token, title, tagList):
        resp = testapp.post_json(url_for('articles.make_article'), {
            "article": {
                "title": title,
                "description": "desc",
                "body": "body",
                "tagList": tagList,
            }
        }, headers={'Authorization': 'Token {}'.format(token)})
        return resp.json['article']['slug']

    def test_related_articles_prioritizes_shared_tags(self, testapp, user):
        author1 = user.get()
        author2 = user.get()
        token1 = self._login_token(testapp, author1)
        token2 = self._login_token(testapp, author2)

        source = self._make_article(testapp, token1, "Source", ["python", "flask"])
        # different author, shares one tag with the source
        shared_tag = self._make_article(testapp, token2, "Shared Tag", ["python"])
        # same author as the source, no tag in common
        same_author = self._make_article(testapp, token1, "Same Author", ["java"])
        # neither shares a tag nor the author -> must not show up
        unrelated = self._make_article(testapp, token2, "Unrelated", ["rust"])

        resp = testapp.get(url_for('articles.get_related_articles', slug=source),
                           headers={'Authorization': 'Token {}'.format(token1)})

        slugs = [a['slug'] for a in resp.json['articles']]
        assert resp.json['articlesCount'] == 2
        assert source not in slugs            # the source is never recommended
        assert unrelated not in slugs         # nothing random sneaks in
        assert shared_tag in slugs
        assert same_author in slugs
        # shared tags outranks merely sharing the author
        assert slugs.index(shared_tag) < slugs.index(same_author)

    def test_related_articles_excludes_self(self, testapp, user):
        author = user.get()
        token = self._login_token(testapp, author)
        source = self._make_article(testapp, token, "Solo Source", ["python"])
        self._make_article(testapp, token, "Sibling", ["python"])

        resp = testapp.get(url_for('articles.get_related_articles', slug=source))
        slugs = [a['slug'] for a in resp.json['articles']]
        assert source not in slugs

    def test_related_articles_respects_limit(self, testapp, user):
        author = user.get()
        token = self._login_token(testapp, author)
        source = self._make_article(testapp, token, "Limit Source", ["python"])
        for i in range(4):
            self._make_article(testapp, token, "Related {}".format(i), ["python"])

        resp = testapp.get(url_for('articles.get_related_articles', slug=source, limit=2))
        assert resp.json['articlesCount'] == 2
        assert len(resp.json['articles']) == 2

    def test_related_articles_empty_when_none(self, testapp, user):
        author = user.get()
        token = self._login_token(testapp, author)
        source = self._make_article(testapp, token, "Lonely", ["a-very-unique-tag"])

        resp = testapp.get(url_for('articles.get_related_articles', slug=source))
        assert resp.json['articlesCount'] == 0
        assert resp.json['articles'] == []

    def test_related_articles_not_found(self, testapp, user):
        resp = testapp.get(url_for('articles.get_related_articles', slug='no-such-slug'),
                           expect_errors=True)
        assert resp.status_code == 404

    def test_related_articles_available_to_anonymous(self, testapp, user):
        author = user.get()
        token = self._login_token(testapp, author)
        source = self._make_article(testapp, token, "Public Source", ["python"])
        self._make_article(testapp, token, "Public Sibling", ["python"])

        # no Authorization header -> jwt_optional path
        resp = testapp.get(url_for('articles.get_related_articles', slug=source))
        assert resp.status_code == 200
        assert 'articles' in resp.json
        assert all(a['favorited'] is False for a in resp.json['articles'])
