import requests
import hashlib
import hmac
import json
from django.conf import settings


def send_stk_push(phone_number, amount, reference, description):
    """
    Send STK Push via Codian API.
    Production: https://api.codian.co.ke/v1/payments/c2b/initiate/
    """

    url = 'https://api.codian.co.ke/v1/payments/c2b/initiate/'

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        'client_id': settings.CODIAN_CLIENT_ID,
        'client_secret': settings.CODIAN_CLIENT_SECRET,
        'account_number': settings.CODIAN_ACCOUNT_NUMBER,
        'phone': phone_number,
        'amount': int(amount),
        'reference': reference,
        'description': description,
        'callback_url': settings.CODIAN_CALLBACK_URL,
    }

    print(f"[CODIAN STK] URL: {url}")
    print(f"[CODIAN STK] Payload: {json.dumps(payload)}")

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        print(f"[CODIAN STK] Status: {response.status_code}")
        print(f"[CODIAN STK] Response: {response.text}")

        if not response.text.strip():
            return False, {'message': 'Empty response from Codian.'}

        data = response.json()

        if response.status_code in [200, 201] and data.get('success'):
            return True, data
        else:
            return False, {'message': data.get('error', data.get('message', 'STK Push failed'))}

    except requests.exceptions.Timeout:
        return False, {'message': 'STK Push timed out. Try again.'}
    except requests.exceptions.ConnectionError:
        return False, {'message': 'Cannot connect to Codian. Check internet.'}
    except ValueError:
        return False, {'message': f'Invalid JSON response: {response.text}'}
    except Exception as e:
        return False, {'message': str(e)}


def verify_callback_signature(request_body, received_signature):
    """Verify callback is genuinely from Codian."""
    secret = settings.CODIAN_SIGNATURE_SECRET.encode()
    expected = hmac.new(
        secret,
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature)