from rest_framework import serializers
from shipment.models import ShipmentHistory



class ShipmentHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model = ShipmentHistory
        fields = '__all__'
