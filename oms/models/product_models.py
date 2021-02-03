# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class LabProduct(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.sku + ' -> ' + self.name

    INDEX_CHOICES = (
        ('', '-'),
        ('1.50', '1.50'),
        ('1.56', '1.56'),
        ('1.59', '1.59'),
        ('1.61', '1.61'),
        ('1.67', '1.67'),
        ('1.74', '1.74')
    )
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OLPR', editable=False)
    product_id = models.CharField(u'Product Id', max_length=128, default='', null=True, blank=True)
    sku = models.CharField(u'SKU', max_length=128, default='', null=True, unique=True)  # 该属性必须唯一
    name = models.CharField(u'Name', max_length=1024, default='', null=True)

    #jo-14
    index = models.CharField(u'折射率', max_length=40, null=False, blank=False, default='', choices=INDEX_CHOICES)

    is_rx_lab = models.BooleanField(u'Is Rx Lab',default=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

class PgProduct(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.sku + ' -> ' + self.name

    INDEX_CHOICES = (
        ('', '-'),
        ('1.50', '1.50'),
        ('1.56', '1.56'),
        ('1.59', '1.59'),
        ('1.61', '1.61'),
        ('1.67', '1.67'),
        ('1.74', '1.74')
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OPPR', editable=False)
    product_id = models.CharField(u'Product Id', max_length=128, default='', null=True, blank=True)
    sku = models.CharField(u'SKU', max_length=128, default='', null=True, unique=True)  # 该属性必须唯一
    name = models.CharField(u'Name', max_length=1024, default='', null=True,blank=True)

    lab_product=models.ForeignKey(LabProduct, null=True, blank=True)

    #jo-14
    index = models.CharField(u'折射率', max_length=40, null=False, blank=False, default='', choices=INDEX_CHOICES)

    is_rx_lab = models.BooleanField(u'Is Rx Lab', default=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)