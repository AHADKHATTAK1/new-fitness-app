"""
Professional Payment Gateway Manager
Handles JazzCash, EasyPaisa, and Stripe payments with unified interface
"""

import os
import hashlib
import hmac
import time
import stripe
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')


class PaymentManager:
    """Unified payment gateway manager for multiple providers"""
    
    def __init__(self):
        # JazzCash Configuration
        self.jazzcash_merchant_id = os.getenv('JAZZCASH_MERCHANT_ID', '')
        self.jazzcash_password = os.getenv('JAZZCASH_PASSWORD', '')
        self.jazzcash_integrity_salt = os.getenv('JAZZCASH_INTEGRITY_SALT', '')
        self.jazzcash_url = os.getenv('JAZZCASH_URL', 'https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/')
        
        # EasyPaisa Configuration
        self.easypaisa_store_id = os.getenv('EASYPAISA_STORE_ID', '')
        self.easypaisa_hash_key = os.getenv('EASYPAISA_HASH_KEY', '')
        self.easypaisa_url = os.getenv('EASYPAISA_URL', 'https://easypay.easypaisa.com.pk/easypay/Index.jsf')
        
        # Stripe Configuration
        self.stripe_public_key = os.getenv('STRIPE_PUBLIC_KEY', '')
        self.stripe_secret_key = os.getenv('STRIPE_SECRET_KEY', '')
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
    
    # ==================== JAZZCASH METHODS ====================
    
    def generate_jazzcash_hash(self, params: Dict) -> str:
        """Generate secure hash for JazzCash transaction"""
        sorted_string = '&'.join([str(params[key]) for key in sorted(params.keys()) if params[key]])
        sorted_string = self.jazzcash_integrity_salt + '&' + sorted_string
        return hmac.new(
            self.jazzcash_integrity_salt.encode('utf-8'),
            sorted_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def initiate_jazzcash_payment(self, amount: float, user_email: str, 
                                   return_url: str) -> Dict:
        """
        Initiate JazzCash payment
        Returns form data to POST to JazzCash
        """
        # Generate unique transaction reference
        txn_ref = f"T{int(time.time())}{user_email[:5]}"
        txn_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
        expiry_datetime = (datetime.now() + timedelta(hours=1)).strftime('%Y%m%d%H%M%S')
        
        # Convert amount to paisa (smallest unit)
        amount_paisa = int(amount * 100)
        
        params = {
            'pp_Version': '1.1',
            'pp_TxnType': 'MWALLET',
            'pp_Language': 'EN',
            'pp_MerchantID': self.jazzcash_merchant_id,
            'pp_Password': self.jazzcash_password,
            'pp_TxnRefNo': txn_ref,
            'pp_Amount': amount_paisa,
            'pp_TxnCurrency': 'PKR',
            'pp_TxnDateTime': txn_datetime,
            'pp_BillReference': f"GYM-{txn_ref}",
            'pp_Description': 'Gym Membership Subscription',
            'pp_TxnExpiryDateTime': expiry_datetime,
            'pp_ReturnURL': return_url,
            'pp_SecureHash': '',
            'ppmpf_1': user_email,  # Customer email
        }
        
        # Generate secure hash
        params['pp_SecureHash'] = self.generate_jazzcash_hash(params)
        
        return {
            'success': True,
            'provider': 'jazzcash',
            'post_url': self.jazzcash_url,
            'form_data': params,
            'txn_ref': txn_ref
        }
    
    def verify_jazzcash_response(self, response_data: Dict) -> Tuple[bool, str]:
        """
        Verify JazzCash payment callback
        Returns (success, message)
        """
        # Extract hash from response
        received_hash = response_data.get('pp_SecureHash', '')
        
        # Remove hash from params for verification
        params_to_verify = {k: v for k, v in response_data.items() if k != 'pp_SecureHash'}
        
        # Generate expected hash
        expected_hash = self.generate_jazzcash_hash(params_to_verify)
        
        # Verify hash
        if received_hash != expected_hash:
            return False, "Invalid transaction signature"
        
        # Check response code
        response_code = response_data.get('pp_ResponseCode', '')
        if response_code == '000':
            return True, "Payment successful"
        else:
            return False, f"Payment failed: {response_data.get('pp_ResponseMessage', 'Unknown error')}"
    
    # ==================== EASYPAISA METHODS ====================
    
    def generate_easypaisa_hash(self, params: Dict) -> str:
        """Generate secure hash for EasyPaisa transaction"""
        hash_string = '&'.join([str(params[key]) for key in sorted(params.keys()) if params[key]])
        return hashlib.sha256(f"{self.easypaisa_hash_key}&{hash_string}".encode()).hexdigest()
    
    def initiate_easypaisa_payment(self, amount: float, user_email: str,
                                    return_url: str) -> Dict:
        """
        Initiate EasyPaisa payment
        Returns form data to POST to EasyPaisa
        """
        order_id = f"EP{int(time.time())}"
        
        params = {
            'storeId': self.easypaisa_store_id,
            'amount': amount,
            'postBackURL': return_url,
            'orderRefNum': order_id,
            'expiryDate': (datetime.now() + timedelta(hours=2)).strftime('%Y%m%d %H%M%S'),
            'merchantHashedReq': '',
            'autoRedirect': '0',
            'paymentMethod': 'MA_PAYMENT_METHOD',
            'emailAddress': user_email,
        }
        
        # Generate hash
        params['merchantHashedReq'] = self.generate_easypaisa_hash(params)
        
        return {
            'success': True,
            'provider': 'easypaisa',
            'post_url': self.easypaisa_url,
            'form_data': params,
            'order_id': order_id
        }
    
    def verify_easypaisa_response(self, response_data: Dict) -> Tuple[bool, str]:
        """
        Verify EasyPaisa payment callback
        Returns (success, message)
        """
        # Check response code
        response_code = response_data.get('responseCode', '')
        if response_code == '0000':
            return True, "Payment successful"
        else:
            return False, f"Payment failed: {response_data.get('responseDesc', 'Unknown error')}"
    
    # ==================== STRIPE METHODS ====================
    
    def create_stripe_checkout_session(self, amount: float, user_email: str,
                                       success_url: str, cancel_url: str,
                                       client_reference_id: Optional[str] = None,
                                       metadata: Optional[Dict] = None) -> Dict:
        """
        Create Stripe checkout session for credit/debit card payments
        """
        try:
            stripe_metadata = {
                'purpose': 'gym_subscription',
                'email': user_email
            }
            if metadata:
                stripe_metadata.update({k: str(v) for k, v in metadata.items()})

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Gym Membership Subscription',
                            'description': 'Monthly gym membership',
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                client_reference_id=client_reference_id or user_email,
                metadata=stripe_metadata
            )
            
            return {
                'success': True,
                'provider': 'stripe',
                'session_id': session.id,
                'session_url': session.url
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_stripe_payment(self, session_id: str) -> Tuple[bool, str]:
        """
        Verify Stripe payment session
        Returns (success, message)
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                return True, "Payment successful"
            else:
                return False, f"Payment not completed: {session.payment_status}"
        except stripe.error.StripeError as e:
            return False, f"Verification failed: {str(e)}"
    
    # ==================== UNIFIED INTERFACE ====================
    
    def initiate_payment(self, provider: str, amount: float, user_email: str,
                        return_url: str, **kwargs) -> Dict:
        """
        Unified payment initiation method
        
        Args:
            provider: 'jazzcash', 'easypaisa', or 'stripe'
            amount: Payment amount
            user_email: Customer email
            return_url: URL to return after payment
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Dict with payment initiation data
        """
        if provider == 'jazzcash':
            return self.initiate_jazzcash_payment(amount, user_email, return_url)
        elif provider == 'easypaisa':
            return self.initiate_easypaisa_payment(amount, user_email, return_url)
        elif provider == 'stripe':
            success_url = kwargs.get('success_url', return_url)
            cancel_url = kwargs.get('cancel_url', return_url)
            client_reference_id = kwargs.get('client_reference_id', user_email)
            metadata = kwargs.get('metadata', None)
            return self.create_stripe_checkout_session(
                amount,
                user_email,
                success_url,
                cancel_url,
                client_reference_id=client_reference_id,
                metadata=metadata
            )
        else:
            return {
                'success': False,
                'error': f'Unknown payment provider: {provider}'
            }
    
    def verify_payment(self, provider: str, response_data: Dict) -> Tuple[bool, str]:
        """
        Unified payment verification method
        
        Args:
            provider: 'jazzcash', 'easypaisa', or 'stripe'
            response_data: Payment provider response
        
        Returns:
            (success: bool, message: str)
        """
        if provider == 'jazzcash':
            return self.verify_jazzcash_response(response_data)
        elif provider == 'easypaisa':
            return self.verify_easypaisa_response(response_data)
        elif provider == 'stripe':
            session_id = response_data.get('session_id', '')
            return self.verify_stripe_payment(session_id)
        else:
            return False, f'Unknown payment provider: {provider}'
