# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import models

class HolidaySetting(models.Model):
    def __str__(self):
        return str(self.id) + ':' + self.type

    COUNTRY_ID_CHOICES = (
        ('CN','CN'),
        ('US','US')
    )

    type = models.CharField(u'Type', max_length=20, default='HOSE', editable=False)  # 操作日志

    country_id = models.CharField(u'Country Id', max_length=20, null=True, blank=True,default='CN',choices=COUNTRY_ID_CHOICES)
    holiday_date = models.DateField(u'Holiday Date', null=True, blank=True)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)


    def holiday(self,begin_date):
        querysets = HolidaySetting.objects.filter(country_id='US',holiday_date__gte=begin_date)
        us_holiday = []
        for queryset in querysets:
            us_holiday.append(queryset.holiday_date.strftime("%Y-%m-%d"))
        return us_holiday


    def add_holiday(self,holiday,country = 'US'):
        self.country_id = country
        self.holiday_date = holiday
        self.save()

    def query_by_holiday(self,holiday_date):

        holiday_date = HolidaySetting.objects.get(holiday_date = holiday_date)
        return holiday_date