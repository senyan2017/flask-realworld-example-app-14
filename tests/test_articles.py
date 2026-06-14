# coding: utf-8

from flask import url_for
from datetime import datetime


def _login(testapp, user):
    """Helper: log in a user and return their JWT token."""
    resp = testapp.post_json(url_for('user.login_user'), {
        'user': {'email': user.email, 'password': 'myprecious'}
    })
    return str(resp.json['user']['token'])


def _make_article(testapp, token, title, tags=None):
    """Helper: create an article and return the response JSON."""
    payload = {
        "article": {
            "title": title,
            "description": "desc for " + title,
            "body": "body for " + title,
            "tagList": tags or [],
        }
    }
    return testapp.post_json(
        url_for('articles.make_article'), payload,
        headers={'Authorization': 'Token {}'.format(token)}
    )


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


class TestRelatedArticles:
    """Tests for GET /api/articles/<slug>/related."""

    def _setup_users_and_articles(self, testapp, user_fixture):
        """Create two users and a set of articles with known tag overlap."""
        user_a = user_fixture.get()
        user_b = user_fixture.get()
        token_a = _login(testapp, user_a)
        token_b = _login(testapp, user_b)

        # Article A1 by user_a: tags [python, flask, api]
        a1 = _make_article(testapp, token_a, "Flask API guide",
                           ["python", "flask", "api"])
        # Article A2 by user_b: tags [python, flask]           -> 2 shared tags with A1
        a2 = _make_article(testapp, token_b, "Python Flask tips",
                           ["python", "flask"])
        # Article A3 by user_b: tags [python, django]          -> 1 shared tag with A1
        a3 = _make_article(testapp, token_b, "Django vs Flask",
                           ["python", "django"])
        # Article A4 by user_b: tags [react, angular]          -> 0 shared tags with A1
        a4 = _make_article(testapp, token_b, "Frontend frameworks",
                           ["react", "angular"])
        # Article A5 by user_a: tags [python, flask, api, testing] -> 3 shared with A1
        a5 = _make_article(testapp, token_a, "Testing Flask APIs",
                           ["python", "flask", "api", "testing"])

        return {
            'user_a': user_a, 'user_b': user_b,
            'token_a': token_a, 'token_b': token_b,
            'a1': a1, 'a2': a2, 'a3': a3, 'a4': a4, 'a5': a5,
        }

    def test_related_articles_by_shared_tags(self, testapp, user):
        """Related articles should be ordered by tag overlap (desc)."""
        data = self._setup_users_and_articles(testapp, user)
        slug = data['a1'].json['article']['slug']

        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        titles = [a['title'] for a in resp.json['articles']]
        # A5 (3 shared tags) should come before A2 (2), then A3 (1).
        # A4 shares no tags, so it should not appear (or appear last via author fallback).
        assert "Testing Flask APIs" in titles
        assert "Python Flask tips" in titles
        assert "Django vs Flask" in titles
        # The first result should be the one with the most shared tags
        assert titles[0] == "Testing Flask APIs"
        assert titles[1] == "Python Flask tips"

    def test_related_excludes_current_article(self, testapp, user):
        """The source article must never appear in its own related list."""
        data = self._setup_users_and_articles(testapp, user)
        slug = data['a1'].json['article']['slug']

        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        slugs = [a['slug'] for a in resp.json['articles']]
        assert slug not in slugs

    def test_related_fallback_to_same_author(self, testapp, user):
        """When tags yield fewer results than limit, fill with same-author articles."""
        user_a = user.get()
        user_b = user.get()
        token_a = _login(testapp, user_a)
        token_b = _login(testapp, user_b)

        # A1 has unique tags; A2 by same author has completely different tags
        a1 = _make_article(testapp, token_a, "Unique topic A", ["uniqueA"])
        a2 = _make_article(testapp, token_a, "Unique topic B", ["uniqueB"])
        a3 = _make_article(testapp, token_a, "Unique topic C", ["uniqueC"])
        # Another user's article with no overlapping tags
        _make_article(testapp, token_b, "Unrelated", ["zzz"])

        slug = a1.json['article']['slug']
        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        titles = [a['title'] for a in resp.json['articles']]
        # A2 and A3 should appear via same-author fallback
        assert "Unique topic B" in titles
        assert "Unique topic C" in titles
        # The other user's article should not appear
        assert "Unrelated" not in titles

    def test_related_limit_param(self, testapp, user):
        """The limit query parameter should cap the number of results."""
        data = self._setup_users_and_articles(testapp, user)
        slug = data['a1'].json['article']['slug']

        resp = testapp.get(
            url_for('articles.get_related_articles', slug=slug, limit=2)
        )

        assert resp.json['articlesCount'] <= 2
        assert len(resp.json['articles']) <= 2

    def test_related_nonexistent_article_returns_404(self, testapp, user):
        """Requesting related articles for a missing slug must 404."""
        # Ensure the user fixture is initialised so the app context is ready
        user.get()
        resp = testapp.get(
            url_for('articles.get_related_articles', slug='does-not-exist'),
            expect_errors=True,
        )
        assert resp.status_code == 404

    def test_related_empty_when_no_tags_and_no_author_articles(self, testapp, user):
        """An article with no tags and no siblings by the same author returns []."""
        user_a = user.get()
        token_a = _login(testapp, user_a)
        a1 = _make_article(testapp, token_a, "Solo article", [])

        slug = a1.json['article']['slug']
        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        assert resp.json['articles'] == []
        assert resp.json['articlesCount'] == 0

    def test_related_works_for_anonymous_user(self, testapp, user):
        """The endpoint should work without an Authorization header."""
        user_a = user.get()
        token_a = _login(testapp, user_a)
        _make_article(testapp, token_a, "Tagged one", ["common"])
        a2 = _make_article(testapp, token_a, "Tagged two", ["common"])

        slug = a2.json['article']['slug']
        # No auth header at all
        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        assert resp.status_code == 200
        assert resp.json['articlesCount'] >= 1

    def test_related_response_shape_matches_articles_list(self, testapp, user):
        """Response structure should mirror the standard articles list endpoint."""
        user_a = user.get()
        token_a = _login(testapp, user_a)
        a1 = _make_article(testapp, token_a, "Source", ["shared"])
        _make_article(testapp, token_a, "Related one", ["shared"])

        slug = a1.json['article']['slug']
        resp = testapp.get(url_for('articles.get_related_articles', slug=slug))

        # Top-level keys
        assert 'articles' in resp.json
        assert 'articlesCount' in resp.json
        # Each article should have the standard keys
        if resp.json['articles']:
            art = resp.json['articles'][0]
            for key in ('slug', 'title', 'description', 'body',
                        'createdAt', 'updatedAt', 'author', 'tagList',
                        'favoritesCount', 'favorited'):
                assert key in art, "Missing key: {}".format(key)
