# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from django.db import connections
from oms.views import *
class Command(BaseCommand):
    """
    信息同步
    """
    def handle(self, *args, **options):
        pf = product_frame.objects.filter(is_already_synchronous__in=(0,1)).all()
        i = 0
        for p in pf:
            sql = "SELECT * FROM catalog_product_flat_all_1  WHERE stock_sku = '{0}'"
            product_type = product_frame.objects.filter(product_type="FRAME", sku=p.sku).first()
            i += 1
            print('progress rate: --------->', "%.2f%%" % (int(i) / float(len(pf)) * 100))
            try:
                with connections['pg_mg_query'].cursor() as cursor:
                    sql=sql.format(p.sku)
                    cursor.execute(sql)
                    results = namedtuplefetchall(cursor)

                    if (results.__len__() !=0 and product_type):

                        frame_shape_value = results[0].frame_shape_value
                        rim_type_value = results[0].rim_type_value

                        if rim_type_value == 'Full Rim':
                            etyp = '1'
                        elif rim_type_value == 'Rimless':
                            etyp = '2'
                        elif rim_type_value == 'Semi Rimless':
                            etyp = '3'
                        else:
                            pass
                        material_value = results[0].material_value
                        bridge_value = results[0].bridge_value
                        temple_length_value = results[0].temple_length_value
                        attribute_set = results[0].attribute_set_id
                        frame_width_value = results[0].frame_width_value
                        nose_pad = results[0].nose_pad
                        has_spring_hinges = results[0].has_spring_hinges
                        color_changing = results[0].color_changing

                        if not bridge_value:
                            bridge_value = 0
                        else:
                            pass
                        if not temple_length_value:
                            temple_length_value = 0
                        else:
                            pass

                        if not frame_width_value:
                            frame_width_value = 0
                        else:
                            pass
                        if not nose_pad:
                            nose_pad = 0
                        else:
                            pass

                        if not has_spring_hinges:
                            has_spring_hinges = 0
                        else:
                            pass
                        if not color_changing:
                            color_changing = 0
                        else:
                            pass


                        product_num=p.sku[0:4]
                        product_frame.objects.filter(sku=p.sku).update(
                                product_num=product_num,
                                is_has_spring_hinges=has_spring_hinges,
                                is_color_changing =color_changing,
                                fsha=frame_shape_value,
                                dbl=bridge_value,
                                temple=temple_length_value,
                                fmat=material_value,
                                etyp=etyp,
                                attribute_set=attribute_set,
                                frame_width=frame_width_value,
                                is_nose_pad=nose_pad,
                                is_already_synchronous=1
                            )

                        print(p.sku,"accomplish")
            except Exception as e:
                return ''