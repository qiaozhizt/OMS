# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.

class base_type(models.Model):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='BAMO', editable=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'SEQUENCE', default=0)
    is_enabled = models.BooleanField(u'IS Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    comments = models.CharField(u'Comments', max_length=4096, default='', blank=True, null=True)


class comment(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='PGCO', editable=False)

    BIZ_TYPE_CHOICES = (
        ('OPOR', 'Pg Order'),
        ('PORL', 'Pg Order Item'),
        ('OLOR', 'Lab Order'),
    )

    STATUS_CHOICES = (
        ('0', 'New'),
        ('1', 'Processing'),
        ('2', 'Done'),
        ('3', 'Closed'),
    )

    parent_entity = models.ForeignKey('self', models.CASCADE,
                                      blank=True,
                                      null=True, )

    biz_type = models.CharField(u'Biz Type', max_length=20, default='', choices=BIZ_TYPE_CHOICES, null=True,
                                blank=True, )
    biz_id = models.CharField(u'Biz ID', max_length=128, default='', null=True, blank=True, )

    comments = models.TextField(u'Comments', default='', blank=True, null=True)

    status = models.CharField(u'Status', max_length=20, default='0', choices=STATUS_CHOICES, null=True, blank=True, )

    user_name = models.CharField(u'Reporter', max_length=128, default='', blank=True, null=True)
    assign_id = models.CharField(u'Assign ID', max_length=128, default='', blank=True, null=True)
    assign_name = models.CharField(u'Assign', max_length=128, default='', blank=True, null=True)

    @property
    def reviewed(self):
        try:
            objs = comment.objects.filter(parent_entity=self)
            return len(objs)
        except:
            return 0
