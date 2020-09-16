# -*- coding: utf-8 -*-
import json
import re
from unittest import skip, skipIf

import django

asgi_views_supported = django.VERSION >= (3, 1)
if asgi_views_supported:
    from asgiref.sync import sync_to_async
from django.test import TestCase, override_settings, tag

from django.urls import reverse, reverse_lazy

from django.contrib.auth.models import User
import bs4
from test_app.models import (
    TestModel, TestForeignKey, TestM2M,
    TestUUIDModel, TestUUIDForeignKey, TestUUIDM2M
)
from audit.models import CRUDEvent, RequestEvent
from audit.middleware.easyaudit import set_current_user, clear_request


TEST_USER_EMAIL = 'joe@example.com'
TEST_USER_PASSWORD = 'password'
TEST_ADMIN_EMAIL = 'admin@example.com'
TEST_ADMIN_PASSWORD = 'password'


@override_settings(TEST=True)
class TestDjangoCompat(TestCase):

    def test_model_state(self):
        """Ensures models have the internal `_state` object."""
        inst = TestModel()
        self.assertTrue(hasattr(inst, '_state'))


@override_settings(TEST=True)
class TestAuditModels(TestCase):
    Model = TestModel
    FKModel = TestForeignKey
    M2MModel = TestM2M

    def test_create_model(self):
        obj = self.Model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())
        crud_event = crud_event_qs[0]
        data = json.loads(crud_event.object_json_repr)[0]
        self.assertEqual(data['fields']['name'], obj.name)

    def test_fk_model(self):
        obj = self.Model.objects.create()
        obj_fk = self.FKModel.objects.create(name='test', test_fk=obj)
        crud_event = CRUDEvent.objects.filter(object_id=obj_fk.id)[0]
        data = json.loads(crud_event.object_json_repr)[0]
        self.assertEqual(str(data['fields']['test_fk']), str(obj.id))


    @override_settings(DJANGO_EASY_AUDIT_CRUD_EVENT_NO_CHANGED_FIELDS_SKIP=True)
    def test_update_skip_no_changed_fields(self):
        obj = self.Model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())
        obj.name = 'changed name'
        obj.save()
        self.assertEqual(2, crud_event_qs.count())
        last_change = crud_event_qs[1]
        self.assertIn('name', last_change.changed_fields)

    def test_update(self):
        obj = self.Model(name='sree')
        obj.save()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())
        obj.name = 'changed name'
        obj.save()
        obj1 = self.Model.objects.filter(name='changed name')[0]
        self.assertEqual(2, crud_event_qs.count())
        last_change = crud_event_qs[1]
        self.assertIn('name', last_change.changed_fields)

    @override_settings(DJANGO_EASY_AUDIT_CRUD_EVENT_NO_CHANGED_FIELDS_SKIP=True)
    def test_fake_update_skip_no_changed_fields(self):
        obj = self.Model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())

    def test_fake_update(self):
        obj = self.Model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())

    def test_delete(self):
        obj = self.Model.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(1, crud_event_qs.count())

        obj_id = obj.id
        self.Model.objects.get(pk=obj_id).delete()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj_id)
        self.assertEqual(2, crud_event_qs.count())


class TestAuditUUIDModels(TestAuditModels):
    Model = TestUUIDModel
    FKModel = TestUUIDForeignKey
    M2MModel = TestUUIDM2M


@override_settings(TEST=True)
class TestMiddleware(TestCase):
    def _setup_user(self, email, password):
        user = User(username=email)
        user.set_password(password)
        user.save()
        return user

    def _log_in_user(self, email, password):
        login = self.client.login(username=email, password=password)
        self.assertTrue(login)

    def test_middleware_logged_in(self):
        user = self._setup_user(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        self._log_in_user(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        create_obj_url = reverse("test_app:create-obj")
        self.client.post(create_obj_url)
        self.assertEqual(TestModel.objects.count(), 1)
        obj = TestModel.objects.all()[0]
        crud_event = CRUDEvent.objects.filter(object_id=obj.id)[0]
        self.assertEqual(crud_event.user, user)

    def test_middleware_not_logged_in(self):
        create_obj_url = reverse("test_app:create-obj")
        self.client.post(create_obj_url)
        self.assertEqual(TestModel.objects.count(), 1)
        obj = TestModel.objects.all()[0]
        crud_event = CRUDEvent.objects.filter(object_id=obj.id)[0]
        self.assertEqual(crud_event.user, None)

    def test_manual_set_user(self):
        user = self._setup_user(TEST_USER_EMAIL, TEST_USER_PASSWORD)

        # set user/request
        set_current_user(user)
        obj = TestModel.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(crud_event_qs.count(), 1)
        crud_event = crud_event_qs[0]
        self.assertEqual(crud_event.user, user)

    #     # clear request
        clear_request()
        obj = TestModel.objects.create()
        crud_event_qs = CRUDEvent.objects.filter(object_id=obj.id)
        self.assertEqual(crud_event_qs.count(), 1)
        crud_event = crud_event_qs[0]
        self.assertEqual(crud_event.user, None)

    @skip("Test may need a rewrite but the library logic has been rolled back.")
    def test_middleware_logged_in_user_in_request(self):
        user = self._setup_user(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        self.client.force_login(user)
        create_obj_url = reverse("test_app:create-obj")
        self.client.post(create_obj_url)
        self.assertEqual(TestModel.objects.count(), 1)
        obj = TestModel.objects.all()[0]
        crud_event = CRUDEvent.objects.filter(object_id=obj.id)[0]
        self.assertEqual(crud_event.user, user)


@tag("asgi")
@override_settings(TEST=True)
@skipIf(not asgi_views_supported, "Testing ASGI is easier with Django 3.1")
class TestASGIRequestEvent(TestCase):

    def _setup_user(self, email, password):
        user = User.objects.create(username=email)
        user.set_password(password)
        user.save()
        return user

    def _log_in_user(self, email, password):
        login = self.async_client.login(username=email, password=password)
        self.assertTrue(login)

    async def test_login(self):
        user = await sync_to_async(self._setup_user)(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        await sync_to_async(self._log_in_user)(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        self.assertEqual((await sync_to_async(RequestEvent.objects.count)()), 0)
        resp = await self.async_client.get(reverse_lazy("test_app:index"))
        self.assertEqual(resp.status_code, 200)
        assert (await sync_to_async(RequestEvent.objects.get)(user=user))
        # asyncio and transactions do not mix all that well, so here we are performing manual cleanup of the objects
        # created within this test
        await sync_to_async(user.delete)()
        await sync_to_async(RequestEvent.objects.all().delete)()



