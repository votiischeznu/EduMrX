import hashlib

from django.conf import settings


class ClickPaymentService:
    def __init__(self):
        # settings.py faylingizda ushbu kalitlar bo'lishi kerak
        self.merchant_id = getattr(settings, "CLICK_MERCHANT_ID", "your_merchant_id")
        self.service_id = getattr(settings, "CLICK_SERVICE_ID", "your_service_id")
        self.secret_key = getattr(settings, "CLICK_SECRET_KEY", "your_secret_key")
        self.base_url = "https://my.click.uz/services/pay"

    def create_payment_link(self, payment):
        """
        To'lov uchun Click linkini generatsiya qiladi.
        payment: Payment model obyekti
        """
        # Click uchun parametrlarni shakllantirish
        amount = str(float(payment.final_amount))
        merchant_trans_id = str(payment.id)  # Sizning bazadagi to'lov ID

        # Click linkini yaratish
        # Formula: https://my.click.uz/services/pay?service_id=...&merchant_id=...&amount=...&transaction_param=...

        params = {
            "service_id": self.service_id,
            "merchant_id": self.merchant_id,
            "amount": amount,
            "transaction_param": merchant_trans_id,
        }

        query_string = (
            f"service_id={self.service_id}"
            f"&merchant_id={self.merchant_id}"
            f"&amount={amount}"
            f"&transaction_param={merchant_trans_id}"
        )

        # Click linkini qaytarish
        return f"{self.base_url}?{query_string}"
