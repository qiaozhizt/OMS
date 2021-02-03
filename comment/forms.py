# -*- coding: utf-8 -*-

from django import forms
from django.forms import fields
from django.forms import widgets
from django.contrib.auth import get_user_model
User = get_user_model()

from .models import comment


class form_comments_create(forms.Form):
    biz_type=fields.ChoiceField(choices=comment.BIZ_TYPE_CHOICES,widget=forms.Select(attrs={'class': 'form-control'}))
    biz_id = forms.CharField(label='Biz ID', max_length=128,widget=forms.TextInput(attrs={'class': 'form-control'}))
    comments = forms.CharField(label='Comments', max_length=4096,widget=forms.Textarea(attrs={'class': 'form-control'}))
    status = fields.ChoiceField(choices=comment.STATUS_CHOICES,widget=forms.Select(attrs={'class': 'form-control'}))

    assign = fields.IntegerField(
        label='Assign', required=True,
        widget=widgets.Select(attrs={'class': 'form-control'},
                              choices=User.objects.values_list('id', 'username')))

class form_comments_reviwed(forms.Form):
    comments = forms.CharField(label='Comments', max_length=4096,widget=forms.Textarea(attrs={'class': 'form-control'}))

    assign = fields.IntegerField(
        label='Assign', required=True,
        widget=widgets.Select(attrs={'class': 'form-control'},
                              choices=User.objects.values_list('id', 'username')))