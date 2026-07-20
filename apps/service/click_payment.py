import hashlib
from urllib.parse import urlencode

from django.conf import settings


class ClickPaymentService:
    def __init__(self):
        # settings.py faylingizda ushbu kalitlar bo'lishi kerak
        self.merchant_id = getattr(settings, "CLICK_MERCHANT_ID", "your_merchant_id")
        self.service_id = getattr(settings, "CLICK_SERVICE_ID", "your_service_id")
        self.secret_key = getattr(settings, "CLICK_SECRET_KEY", "your_secret_key")
        self.base_url = "https://my.click.uz/services/pay"

    def _generate_signature(self, amount: str, merchant_trans_id: str) -> str:
        # Example signature generation (adjust based on Click API requirements)
        # Usually: md5(merchant_trans_id + secret_key + service_id + merchant_id + amount)
        # or hmac(secret_key, ...)
        
        # Simplified example, should be replaced with actual Click formula
        data = f"{merchant_trans_id}{self.secret_key}{self.service_id}{self.merchant_id}{amount}"
        return hashlib.md5(data.encode()).hexdigest()

    def create_payment_link(self, payment):
        """
        To'lov uchun Click linkini generatsiya qiladi.
        payment: Payment model obyekti
        """
        # Click uchun parametrlarni shakllantirish
        amount = str(float(payment.final_amount))
        merchant_trans_id = str(payment.id)
        
        signature = self._generate_signature(amount, merchant_trans_id)

        # Click linkini yaratish
        # Formula: https://my.click.uz/services/pay?service_id=...&merchant_id=...&amount=...&transaction_param=...&signature=...

        params = {
            "service_id": self.service_id,
            "merchant_id": self.merchant_id,
            "amount": amount,
            "transaction_param": merchant_trans_id,
            "signature": signature,
        }

        query_string = urlencode(params)

        # Click linkini qaytarish
        return f"{self.base_url}?{query_string}"
