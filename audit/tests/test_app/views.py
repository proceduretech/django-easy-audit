from datetime import datetime

from django.http import HttpResponse
from test_app.models import TestModel, TestUUIDModel


def create_obj(Model):
    return Model.objects.create()


def update_obj(Model, pk, name):
    tm = Model.objects.get(pk=pk)
    tm.name = name
    tm.save()
    return tm


def create_obj_view(request):
    obj = create_obj(TestModel)
    return HttpResponse(obj.id)


def index(request):
    return HttpResponse()


def update_obj_view(request):
    name = datetime.now().isoformat()
    return HttpResponse(update_obj(
        TestModel, request.GET['id'], name
    ).id)


def create_uuid_obj_view(request):
    return HttpResponse(create_obj(TestUUIDModel).id)


def update_uuid_obj_view(request):
    name = datetime.now().isoformat()
    return HttpResponse(update_obj(
        TestUUIDModel, request.GET['id'], name
    ).id)


