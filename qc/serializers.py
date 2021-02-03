from rest_framework import serializers
from qc.models import laborder_accessories


class LaborderAccessoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = laborder_accessories
        fields = '__all__'
