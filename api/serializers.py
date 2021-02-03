from rest_framework import serializers
from oms.models.order_models import PgOrderItem


class PgOrderItemSerializers(serializers.ModelSerializer):
    class Meta:
        model = PgOrderItem
        fields = (
            'id', 'type', 'chanel', 'is_vip', 'order_number', 'order_date', 'lab_order_number', 'comments', 'frame',
            'name', 'size', 'quantity', 'lens_sku', 'lens_name', 'coating_sku', 'coating_name', 'tint_sku', 'tint_name',
            'profile_prescription_id', 'od_sph', 'od_cyl', 'od_axis', 'os_sph', 'os_cyl', 'os_axis', 'pd',
            'is_singgle_pd', 'od_pd', 'os_pd', 'od_add', 'os_add', 'od_prism', 'od_base', 'sequence', 'create_at',
            'update_at', 'is_enabled', 'lab_order_entity_id', 'product_index', 'ship_direction', 'bridge', 'city',
            'country', 'lens_width', 'region', 'shipping_description', 'shipping_method', 'temple_length',
            'prescription_id', 'prescription_name', 'prescription_type', 'used_for', 'is_shiped_api', 'qty_ordered',
            'base_discount_amount_item', 'estimated_date', 'estimated_ship_date', 'final_date', 'order_datetime',
            'original_price', 'price', 'promised_ship_date', 'targeted_ship_date', 'pg_order_entity_id', 'status',
            'item_id', 'product_id', 'image', 'lens_height', 'thumbnail', 'instruction', 'profile_id',
            'order_image_urls', 'pupils_position', 'pupils_position_name', 'profile_name', 'asmbl_seght', 'lens_seght',
            'comments_inner', 'comments_ship', 'dia_1', 'dia_2', 'pal_design_name', 'pal_design_sku',
            'progressive_type', 'color', 'frame_type', 'lab_seg_height', 'special_handling', 'assemble_height',
            'special_handling_name', 'special_handling_sku', 'sub_mirrors_height', 'channel', 'od_base1', 'od_prism1',
            'os_base1', 'os_prism1', 'is_has_nose_pad', 'is_has_imgs', 'clipon_qty', 'coatings'
        )


class PgOrderItem_IsHasImgsSerializers(serializers.ModelSerializer):
    class Meta:
        model = PgOrderItem
        fields = (
            'order_number', 'item_id', 'is_has_imgs',
        )
