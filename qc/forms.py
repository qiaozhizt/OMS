# -*- coding: utf-8 -*-

from django import forms
from django.forms import fields
from django.forms import widgets
from django.contrib.auth import get_user_model
from django.forms import ModelForm

User = get_user_model()
from oms.models import choices_models

from .models import glasses_final_inspection_technique, glasses_final_inspection_visual


class form_glasses_final_inspection_technique_create(forms.Form):

    lab_number = forms.CharField(label='Lab Order Number',
                                 required=False,
                                 widget=forms.HiddenInput())

    pd = fields.DecimalField(label='双眼 PD',
                             required=False,
                             initial=0,
                             widget=forms.NumberInput())

    is_singgle_pd = fields.BooleanField(label='单PD',
                                        required=False,
                                        initial=False, widget=forms.NullBooleanSelect())

    od_pd = fields.DecimalField(label='右眼 PD',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    os_pd = fields.DecimalField(label='左眼 PD',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    od_asmbl_seght = fields.DecimalField(label='加工瞳高 OD',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    os_asmbl_seght = fields.DecimalField(label='加工瞳高 OS',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    od_prism = fields.DecimalField(label='右眼 Prism',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=2,
                                widget=forms.NumberInput())

    od_base = fields.DecimalField(label='右眼 Base',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=2,
                                widget=forms.NumberInput())

    os_prism = fields.DecimalField(label='左眼 Prism',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=2,
                                widget=forms.NumberInput())

    os_base = fields.DecimalField(label='左眼 Base',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=2,
                                widget=forms.NumberInput())

    od_prism1 = fields.DecimalField(label='右眼2 Prism',
                                   required=False,
                                   initial=0,
                                   max_digits=5,
                                   decimal_places=2,
                                   widget=forms.NumberInput())

    od_base1 = fields.DecimalField(label='右眼2 Base',
                                  required=False,
                                  initial=0,
                                  max_digits=5,
                                  decimal_places=2,
                                  widget=forms.NumberInput())

    os_prism1 = fields.DecimalField(label='左眼2 Prism',
                                   required=False,
                                   initial=0,
                                   max_digits=5,
                                   decimal_places=2,
                                   widget=forms.NumberInput())

    os_base1 = fields.DecimalField(label='左眼2 Base',
                                  required=False,
                                  initial=0,
                                  max_digits=5,
                                  decimal_places=2,
                                  widget=forms.NumberInput())

    blue_blocker = fields.BooleanField(required=False,
                                       initial=False,
                                       label='镜片抗蓝光',
                                       widget=forms.NullBooleanSelect())

    polarized = fields.BooleanField(required=False,
                                    initial=False,
                                    label='镜片偏光',
                                    widget=forms.NullBooleanSelect())

    light_responsive = fields.BooleanField(required=False,
                                           initial=False,
                                           label='镜片膜变',
                                           widget=forms.NullBooleanSelect())

    light_responsive_color = fields.ChoiceField(required=False,
                                                initial=False,
                                                label='变色颜色', choices=choices_models.LENS_COLOR_CHOICES,
                                                widget=forms.Select())

    co = fields.BooleanField(required=False,
                             initial=False,
                             label='超防水涂层',
                             widget=forms.NullBooleanSelect())

    tint = fields.BooleanField(required=False,
                               initial=False,
                               label='染色',
                               widget=forms.NullBooleanSelect())

    tint_deepness = fields.DecimalField(label='染色深度',
                                required=False,
                                initial=0,
                                max_digits=4,
                                decimal_places=0,
                                widget=forms.NumberInput())

    is_gradient = fields.BooleanField(required=False,
                                       initial=False,
                                       label='渐变染色',
                                       widget=forms.NullBooleanSelect())

    is_d_thin = fields.BooleanField(required=False,
                                       initial=False,
                                       label='是否美薄',
                                       widget=forms.NullBooleanSelect())

    is_qualified = fields.BooleanField(label='是否合格',
                                       required=False,
                                       initial=False,
                                       widget=forms.NullBooleanSelect())

    comments = forms.CharField(label='备注',
                               required=False,
                               max_length=4096,
                               widget=forms.Textarea(attrs={'class': 'form-control'}))


    assembler_id = fields.IntegerField(label='assembler_id',
                                       required=False,
                                       widget=forms.Select())

    # add lee 2020.8.4
    cutting_edge_user_id = fields.IntegerField(label='割边师',
                                       required=False,
                                       widget=forms.Select())
    beauty_user_id = fields.IntegerField(label='整型师',
                                       required=False,
                                       widget=forms.Select())
    # end

    od_sub_mirrors_height = fields.DecimalField(label='右眼子镜高',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    os_sub_mirrors_height = fields.DecimalField(label='左眼子镜高',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())

    is_special_handling = fields.BooleanField(label='加工要求是否合格',
                                       required=False,
                                       initial=False,
                                       widget=forms.NullBooleanSelect())
    od_tint_deepness = fields.DecimalField(label='右片染色深度',
                                required=False,
                                initial=0,
                                max_digits=4,
                                decimal_places=0,
                                widget=forms.NumberInput())

    os_tint_deepness = fields.DecimalField(label='左片染色深度',
                                required=False,
                                initial=0,
                                max_digits=4,
                                decimal_places=0,
                                widget=forms.NumberInput())

    clipon_qty = fields.DecimalField(label='夹片',
                                         required=False,
                                         initial=0,
                                         max_digits=5,
                                         decimal_places=1,
                                         widget=forms.NumberInput())
    is_polishing = fields.BooleanField(label='是否抛光',
                                       required=False,
                                       initial=False,
                                       widget=forms.NullBooleanSelect())
    is_near_light = fields.BooleanField(label='近光区是否完整',
                                       required=False,
                                       initial=False,
                                       widget=forms.NullBooleanSelect())
    coatings = fields.CharField(label='膜层')
    npd = fields.DecimalField(label='双眼 NPD',
                             required=False,
                             initial=0,
                             widget=forms.NumberInput())
    od_npd = fields.DecimalField(label='右眼 NPD',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())
    os_npd = fields.DecimalField(label='左眼 NPD',
                                required=False,
                                initial=0,
                                max_digits=5,
                                decimal_places=1,
                                widget=forms.NumberInput())
