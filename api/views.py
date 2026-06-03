from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from decimal import Decimal

from .serializers import *
from accounts.models import User
from investments.models import Investment
from withdrawals.models import Withdrawal
from referrals.models import Referral
from notifications.models import Notification
from payments.models import Payment
from payments.mpesa import send_stk_push
from game.models import GameRound, GameEntry
from aviator.models import AviatorRound, AviatorBet
from aviator.views import get_or_create_round, process_auto_cashouts
import uuid


# ── AUTH ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })
    return Response({
        'success': False,
        'error': 'Invalid username or password.'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    return Response({
        'success': True,
        'user': UserSerializer(request.user).data,
    })


# ── DASHBOARD ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user

    total_invested = sum(
        i.amount for i in Investment.objects.filter(
            user=user, status__in=['active', 'matured']
        )
    )
    total_earned = sum(
        i.profit for i in Investment.objects.filter(
            user=user, status='matured'
        )
    )
    total_referral_earnings = sum(
        r.bonus_amount for r in Referral.objects.filter(
            referrer=user, bonus_paid=True
        )
    )

    scheme = request.scheme
    host = request.get_host()
    referral_link = f"{scheme}://{host}/accounts/register/?ref={user.referral_code}"

    return Response({
        'wallet_balance': float(user.wallet_balance),
        'total_invested': float(total_invested),
        'total_earned': float(total_earned),
        'total_referral_earnings': float(total_referral_earnings),
        'total_referrals': user.get_total_referrals(),
        'referral_code': user.referral_code,
        'referral_link': referral_link,
        'is_activated': user.is_activated,
    })


# ── PAYMENTS ──────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_account(request):
    user = request.user
    if user.is_activated:
        return Response({'success': False, 'error': 'Already activated.'})

    phone = request.data.get('phone_number', user.phone_number)
    reference = f"ACT-{uuid.uuid4().hex[:10].upper()}"

    payment = Payment.objects.create(
        user=user,
        payment_type='activation',
        amount=settings.ACTIVATION_FEE,
        phone_number=phone,
        reference=reference,
        description='Earnnest Account Activation',
    )

    success, response = send_stk_push(
        phone_number=phone,
        amount=settings.ACTIVATION_FEE,
        reference=reference,
        description='Earnnest Account Activation'
    )

    if success:
        payment.checkout_request_id = response.get('checkout_request_id', '')
        payment.save()
        return Response({
            'success': True,
            'message': f'STK Push sent to {phone}. Enter M-Pesa PIN.',
            'reference': reference,
        })

    payment.status = 'failed'
    payment.save()
    return Response({
        'success': False,
        'error': response.get('message', 'STK Push failed.')
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def topup_wallet(request):
    user = request.user
    amount = request.data.get('amount')
    phone = request.data.get('phone_number', user.phone_number)

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid amount.'})

    if amount < 10:
        return Response({'success': False, 'error': 'Minimum top up is Ksh 10.'})

    reference = f"TOP-{uuid.uuid4().hex[:10].upper()}"
    payment = Payment.objects.create(
        user=user,
        payment_type='topup',
        amount=amount,
        phone_number=phone,
        reference=reference,
        description=f'Earnnest Wallet Top Up - Ksh {amount}',
    )

    success, response = send_stk_push(
        phone_number=phone,
        amount=amount,
        reference=reference,
        description=f'Earnnest Wallet Top Up Ksh {amount}'
    )

    if success:
        payment.checkout_request_id = response.get('checkout_request_id', '')
        payment.save()
        return Response({
            'success': True,
            'message': f'STK Push sent to {phone}.',
            'reference': reference,
        })

    payment.status = 'failed'
    payment.save()
    return Response({
        'success': False,
        'error': response.get('message', 'Top up failed.')
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, reference):
    try:
        payment = Payment.objects.get(
            reference=reference,
            user=request.user
        )
        user = request.user
        # Refresh from DB
        user.refresh_from_db()
        return Response({
            'status': payment.status,
            'wallet_balance': float(user.wallet_balance),
            'is_activated': user.is_activated,
        })
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found.'}, status=404)


# ── INVESTMENTS ───────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def investment_list(request):
    investments = Investment.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return Response(InvestmentSerializer(investments, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_investment(request):
    user = request.user
    amount = request.data.get('amount')

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid amount.'})

    if amount < settings.MIN_INVESTMENT:
        return Response({
            'success': False,
            'error': f'Minimum investment is Ksh {settings.MIN_INVESTMENT}.'
        })

    if user.wallet_balance < amount:
        shortfall = amount - user.wallet_balance
        return Response({
            'success': False,
            'error': f'Insufficient balance. Top up Ksh {shortfall} more.',
            'shortfall': float(shortfall),
        })

    user.wallet_balance -= Decimal(str(amount))
    user.save()

    investment = Investment.objects.create(user=user, amount=amount)
    return Response({
        'success': True,
        'investment': InvestmentSerializer(investment).data,
        'wallet_balance': float(user.wallet_balance),
    })


# ── WITHDRAWALS ───────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def withdrawal_list(request):
    withdrawals = Withdrawal.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return Response(WithdrawalSerializer(withdrawals, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_withdrawal(request):
    user = request.user
    amount = request.data.get('amount')
    phone = request.data.get('phone_number', user.phone_number)
    source = request.data.get('source', 'wallet')

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid amount.'})

    if amount < 500:
        return Response({
            'success': False,
            'error': 'Minimum withdrawal is Ksh 500.'
        })

    if source == 'wallet':
        if amount > user.wallet_balance:
            return Response({
                'success': False,
                'error': f'Insufficient balance. Available: Ksh {user.wallet_balance}'
            })
        user.wallet_balance -= Decimal(str(amount))
        user.save()

    withdrawal = Withdrawal.objects.create(
        user=user,
        amount=amount,
        phone_number=phone,
        status='pending',
    )

    Notification.objects.create(
        user=user,
        notification_type='general',
        title='Withdrawal Submitted',
        message=f'Your withdrawal of Ksh {amount} to {phone} is being processed.'
    )

    return Response({
        'success': True,
        'withdrawal': WithdrawalSerializer(withdrawal).data,
        'wallet_balance': float(user.wallet_balance),
    })


# ── REFERRALS ─────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def referral_list(request):
    referrals = Referral.objects.filter(
        referrer=request.user
    ).order_by('-created_at')
    total_earned = sum(r.bonus_amount for r in referrals if r.bonus_paid)
    return Response({
        'referrals': ReferralSerializer(referrals, many=True).data,
        'total_earned': float(total_earned),
        'total_referrals': referrals.count(),
        'referral_code': request.user.referral_code,
    })


# ── NOTIFICATIONS ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]
    unread = notifications.filter(is_read=False).count()
    notifications.filter(is_read=False).update(is_read=True)
    return Response({
        'notifications': NotificationSerializer(notifications, many=True).data,
        'unread_count': unread,
    })


# ── GAME ──────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def game_status(request):
    current_round = GameRound.objects.filter(
        status='open'
    ).order_by('-created_at').first()

    recent_winners = GameRound.objects.filter(
        status='revealed',
        winner__isnull=False
    ).order_by('-revealed_at')[:5]

    user_entry = None
    if current_round:
        entry = GameEntry.objects.filter(
            user=request.user,
            round=current_round
        ).first()
        if entry:
            user_entry = GameEntrySerializer(entry).data

    return Response({
        'current_round': GameRoundSerializer(current_round).data if current_round else None,
        'user_entry': user_entry,
        'recent_winners': [
            {
                'round_id': r.id,
                'winner': r.winner.username,
                'prize_pool': float(r.prize_pool),
                'secret_number': r.secret_number,
            }
            for r in recent_winners
        ],
        'my_entries': GameEntrySerializer(
            GameEntry.objects.filter(
                user=request.user
            ).order_by('-created_at')[:10],
            many=True
        ).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_game_guess(request):
    user = request.user
    guess = request.data.get('guess', '').strip()

    current_round = GameRound.objects.filter(
        status='open'
    ).order_by('-created_at').first()

    if not current_round:
        return Response({'success': False, 'error': 'No active round.'})

    if not guess.isdigit() or len(guess) != 4:
        return Response({'success': False, 'error': 'Enter a valid 4-digit number.'})

    if GameEntry.objects.filter(user=user, round=current_round).exists():
        return Response({'success': False, 'error': 'Already entered this round.'})

    entry_fee = current_round.entry_fee

    if user.wallet_balance < entry_fee:
        return Response({
            'success': False,
            'error': f'Insufficient balance. Need Ksh {entry_fee}.',
            'shortfall': float(entry_fee - user.wallet_balance),
        })

    user.wallet_balance -= entry_fee
    user.save()

    entry = GameEntry.objects.create(
        user=user,
        round=current_round,
        guess=guess,
        entry_fee=entry_fee,
        status='pending',
    )
    current_round.add_to_pool(entry_fee)

    return Response({
        'success': True,
        'entry': GameEntrySerializer(entry).data,
        'wallet_balance': float(user.wallet_balance),
    })


# ── AVIATOR ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def aviator_status(request):
    round = get_or_create_round()
    process_auto_cashouts(round)

    user_bet = AviatorBet.objects.filter(
        user=request.user,
        round=round
    ).first()

    return Response({
        'round_id': round.id,
        'status': round.status,
        'current_multiplier': round.current_multiplier(),
        'crash_point': round.crash_point if round.status == 'crashed' else None,
        'seconds_until_fly': round.seconds_until_fly(),
        'user_bet': AviatorBetSerializer(user_bet).data if user_bet else None,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aviator_bet(request):
    user = request.user
    bet_amount = request.data.get('bet_amount')
    auto_cashout = request.data.get('auto_cashout')

    try:
        bet_amount = Decimal(str(bet_amount))
        if auto_cashout:
            auto_cashout = float(auto_cashout)
    except (ValueError, TypeError):
        return Response({'success': False, 'error': 'Invalid data.'})

    if bet_amount < 5:
        return Response({'success': False, 'error': 'Minimum bet is Ksh 5.'})

    if bet_amount > user.wallet_balance:
        return Response({
            'success': False,
            'error': f'Insufficient balance.'
        })

    round = get_or_create_round()
    if round.status != 'betting':
        return Response({
            'success': False,
            'error': 'Betting closed. Wait for next round.'
        })

    if AviatorBet.objects.filter(user=user, round=round).exists():
        return Response({'success': False, 'error': 'Already placed a bet.'})

    user.wallet_balance -= bet_amount
    user.save()

    bet = AviatorBet.objects.create(
        user=user,
        round=round,
        bet_amount=bet_amount,
        auto_cashout=auto_cashout,
        status='active',
    )

    return Response({
        'success': True,
        'bet': AviatorBetSerializer(bet).data,
        'wallet_balance': float(user.wallet_balance),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aviator_cashout(request):
    user = request.user

    round = AviatorRound.objects.filter(
        status='flying'
    ).order_by('-created_at').first()

    if not round:
        return Response({'success': False, 'error': 'No active round.'})

    bet = AviatorBet.objects.filter(
        user=user, round=round, status='active'
    ).first()

    if not bet:
        return Response({'success': False, 'error': 'No active bet.'})

    multiplier = round.current_multiplier()
    if multiplier >= round.crash_point:
        bet.status = 'lost'
        bet.save()
        return Response({'success': False, 'error': 'Too late! Plane crashed.'})

    from django.utils import timezone
    winnings = Decimal(str(round(float(bet.bet_amount) * multiplier, 2)))
    user.wallet_balance += winnings
    user.save()

    bet.status = 'won'
    bet.cashout_multiplier = multiplier
    bet.winnings = winnings
    bet.cashed_out_at = timezone.now()
    bet.save()

    return Response({
        'success': True,
        'multiplier': multiplier,
        'winnings': float(winnings),
        'wallet_balance': float(user.wallet_balance),
    })
