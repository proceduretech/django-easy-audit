from django.conf import settings
from djongo import models

import uuid


class PrimaryUUIDTimestampModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class CRUDEvent(PrimaryUUIDTimestampModel):
    _DATABASE = "mongo"

    CREATE = 1
    UPDATE = 2
    DELETE = 3
    M2M_CHANGE = 4
    M2M_CHANGE_REV = 5

    TYPES = (
        (CREATE, "Create"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
        (M2M_CHANGE, "Many-to-Many Change"),
        (M2M_CHANGE_REV, "Reverse Many-to-Many Change"),
    )

    event_type = models.SmallIntegerField(choices=TYPES)
    object_id = models.CharField(max_length=255)
    object_repr = models.TextField(null=True, blank=True)
    object_json_repr = models.TextField(null=True, blank=True)
    changed_fields = models.TextField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
    )
    user_pk_as_string = models.CharField(
        max_length=255, null=True, blank=True, help_text="String version of the user pk"
    )

    def is_create(self):
        return self.CREATE == self.event_type

    def is_update(self):
        return self.UPDATE == self.event_type

    def is_delete(self):
        return self.DELETE == self.event_type


class LoginEvent(PrimaryUUIDTimestampModel):
    _DATABASE = "mongo"
    LOGIN = 0
    LOGOUT = 1
    FAILED = 2
    TYPES = (
        (LOGIN, "Login"),
        (LOGOUT, "Logout"),
        (FAILED, "Failed login"),
    )
    login_type = models.SmallIntegerField(choices=TYPES)
    username = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
    )
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)


class RequestEvent(PrimaryUUIDTimestampModel):
    _DATABASE = "mongo"
    url = models.CharField(null=False, db_index=True, max_length=254)
    method = models.CharField(max_length=20, null=False, db_index=True)
    query_string = models.TextField(null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
    )
    remote_ip = models.CharField(max_length=50, null=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
