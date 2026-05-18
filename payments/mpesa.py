import requests
from django.conf import settings


def initiate_stk_push(phone, amount):

    payload = {
        "client_id": settings.CODIAN_CLIENT_ID,
        "client_secret": settings.CODIAN_CLIENT_SECRET,
        "amount": float(amount),
        "phone": phone,
    }

    try:

        response = requests.post(
            settings.CODIAN_API_URL,
            json=payload,
            headers={
                "Content-Type": "application/json"
            },
            timeout=30
        )

        data = response.json()

        if response.status_code == 200 and data.get("success"):

            return {
                "success": True,
                "checkout_id": data.get("CheckoutRequestID"),
                "message": "STK Push initiated",
                "data": data
            }

        return {
            "success": False,
            "message": data.get(
                "error",
                data.get("ResponseDescription", "Unknown error")
            ),
            "data": data
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "message": "Request timeout"
        }

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Connection error"
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }