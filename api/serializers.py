from rest_framework import serializers
from accounts.models import User
from investments.models import Investment
from withdrawals.models import Withdrawal
from referrals.models import Referral
from notifications.models import Notification
from payments.models import Payment
from game.models import GameRound, GameEntry
from aviator.models import AviatorRound, AviatorBet


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone_number',
            'is_activated', 'wallet_balance',
            'referral_code', 'date_joined'
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'referral_code']

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', '')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.wallet_balance = 50  # Free Ksh 50
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                user.referred_by = referrer
            except User.DoesNotExist:
                pass
        user.save()

        # Welcome notification
        from notifications.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='general',
            title='🎉 Welcome to Earnnest!',
            message=(
                f'Hi {user.username}, welcome! '
                f'You have received Ksh 50 free bonus. '
                f'Pay Ksh 200 to activate your account.'
            )
        )
        return user


class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = [
            'id', 'amount', 'profit', 'status',
            'maturity_date', 'created_at'
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'amount', 'phone_number',
            'status', 'created_at'
        ]


class ReferralSerializer(serializers.ModelSerializer):
    referred_username = serializers.CharField(
        source='referred_user.username', read_only=True
    )

    class Meta:
        model = Referral
        fields = [
            'id', 'referred_username',
            'bonus_amount', 'bonus_paid', 'created_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title',
            'message', 'is_read', 'created_at'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_type', 'amount',
            'phone_number', 'status', 'reference', 'created_at'
        ]


class GameRoundSerializer(serializers.ModelSerializer):
    entries_count = serializers.IntegerField(
        source='entries.count', read_only=True
    )
    time_remaining = serializers.CharField(read_only=True)

    class Meta:
        model = GameRound
        fields = [
            'id', 'prize_pool', 'entry_fee',
            'status', 'entries_count', 'time_remaining',
            'created_at'
        ]


class GameEntrySerializer(serializers.ModelSerializer):
    round_id = serializers.IntegerField(source='round.id', read_only=True)
    secret_number = serializers.SerializerMethodField()

    def get_secret_number(self, obj):
        if obj.round.status == 'revealed':
            return obj.round.secret_number
        return None

    class Meta:
        model = GameEntry
        fields = [
            'id', 'round_id', 'guess', 'entry_fee',
            'status', 'secret_number', 'created_at'
        ]


class AviatorRoundSerializer(serializers.ModelSerializer):
    current_multiplier = serializers.FloatField(read_only=True)
    seconds_until_fly = serializers.FloatField(read_only=True)

    class Meta:
        model = AviatorRound
        fields = [
            'id', 'status', 'current_multiplier',
            'seconds_until_fly', 'created_at'
        ]


class AviatorBetSerializer(serializers.ModelSerializer):
    class Meta:
        model = AviatorBet
        fields = [
            'id', 'bet_amount', 'auto_cashout',
            'cashout_multiplier', 'winnings',
            'status', 'created_at'
        ]
