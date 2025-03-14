from django.db import models
from django.utils.text import gettext_lazy as _


class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Institution(models.Model):
    name = models.CharField(_('Name'), max_length=100, unique=True)
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, verbose_name=_('Parent Institution'), blank=True, null=True
    )
    subjects = models.ManyToManyField(Subject, related_name='institutions')

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Person(models.Model):
    class Type(models.TextChoices):
        ADMIN = 'admin', _('Administrator')
        USER = 'user', _('User')
        GUEST = 'guest', _('Guest')

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    bio = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=5, choices=Type.choices, default=Type.USER)
    institution = models.ForeignKey(Institution, related_name='people', on_delete=models.PROTECT)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
