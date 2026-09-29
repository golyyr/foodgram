import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Принимает картинку в формате data-URL base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, encoded = data.split(';base64,')
            extension = header.split('/')[-1]
            if extension == 'jpeg':
                extension = 'jpg'
            decoded = base64.b64decode(encoded)
            data = ContentFile(
                decoded,
                name=f'{uuid.uuid4().hex}.{extension}',
            )
        return super().to_internal_value(data)
