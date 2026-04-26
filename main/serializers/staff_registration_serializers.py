from rest_framework import serializers
from main.models import StaffRegistration


class StaffRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for public staff registration form submission.
    Creates a pending StaffRegistration record.
    """
    class Meta:
        model = StaffRegistration
        fields = [
            'full_name',
            'gender',
            'dob',
            'id_card_type',
            'id_card_number',
            'photo',
            'qid_front',
            'qid_back',
            'mobile',
            'whatsapp',
            'email',
            'qatar_address',
            'india_address',
            'religious_academic_details',
            'academic_details',
            'previous_institution',
            'msr_number',
            'aadhar_number',
        ]

    def create(self, validated_data):
        organization = self.context.get('organization')
        validated_data['organization'] = organization
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)


class StaffRegistrationVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying staff registration status.
    """
    registration_id = serializers.UUIDField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get('registration_id') and not attrs.get('email'):
            raise serializers.ValidationError(
                "Either registration_id or email is required."
            )
        return attrs


class PendingStaffListSerializer(serializers.ModelSerializer):
    """
    Lists pending staff registrations for admin review.
    """
    class Meta:
        model = StaffRegistration
        fields = [
            'id',
            'full_name',
            'gender',
            'mobile',
            'email',
            'status',
            'submission_date',
        ]


class PendingStaffDetailSerializer(serializers.ModelSerializer):
    """
    Complete pending staff registration details for admin review.
    """
    photo_url = serializers.SerializerMethodField()
    qid_front_url = serializers.SerializerMethodField()
    qid_back_url = serializers.SerializerMethodField()

    class Meta:
        model = StaffRegistration
        fields = [
            'id',
            'full_name',
            'gender',
            'dob',
            'id_card_type',
            'id_card_number',
            'photo_url',
            'qid_front_url',
            'qid_back_url',
            'mobile',
            'whatsapp',
            'email',
            'qatar_address',
            'india_address',
            'religious_academic_details',
            'academic_details',
            'previous_institution',
            'msr_number',
            'aadhar_number',
        ]

    def get_photo_url(self, obj):
        return obj.photo.url if obj.photo else None

    def get_qid_front_url(self, obj):
        return obj.qid_front.url if obj.qid_front else None

    def get_qid_back_url(self, obj):
        return obj.qid_back.url if obj.qid_back else None
