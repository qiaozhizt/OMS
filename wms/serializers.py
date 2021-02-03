from rest_framework import serializers
from wms.models import inventory_receipt_lens,inventory_struct_lens_batch


class InventoryReceiptLensSerializers(serializers.ModelSerializer):
    class Meta:
        model = inventory_receipt_lens
        fields = '__all__'


class InventoryStructLensSerializers(serializers.ModelSerializer):
    class Meta:
        model = inventory_struct_lens_batch
        fields = '__all__'
