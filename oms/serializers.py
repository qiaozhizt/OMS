from rest_framework import serializers
from oms.models.order_models import LabOrder


class LabOrderSerializers(serializers.ModelSerializer):
    class Meta:
        model = LabOrder
        fields = '__all__'
