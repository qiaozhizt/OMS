# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class Shipping(models.Model):

    def __str__(self):
        return str(self.id) + ' : ' + self.order_id

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('US', 'US'),
        ('CN', 'CN'),
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SHIP', editable=False)  # 订单


    order_id = models.CharField(u'Order Id', max_length=128, null=False, blank=False, unique=True)
    lab_order_id = models.CharField(u'Lab Order Id', max_length=4000, null=False, blank=False)

    create_date = models.DateField(u'Create Date',null=True,blank=True)
    first_name = models.CharField(u'First Name',max_length=128, null=False, blank=False)
    last_name = models.CharField(u'Last Name',max_length=128, null=True, blank=True)
    postcode = models.CharField(u'Postcode',max_length=20, null=False, blank=False)
    street = models.CharField(u'Street',max_length=1024, null=False, blank=False)
    city = models.CharField(u'City',max_length=60, null=False, blank=False)
    region = models.CharField(u'Region',max_length=60, null=False, blank=False)
    country_id = models.CharField(u'Country Id',max_length=20, null=False, blank=False)
    telephone = models.CharField(u'Telephone',max_length=20, null=True, blank=True)
    comment = models.TextField(u'Comment',max_length=4000, null=True, blank=True)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

