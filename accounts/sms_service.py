"""
SMS Service for WallpaperHub
Handles SMS sending via multiple providers (Twilio, AWS SNS, etc.)
"""
import os
import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import re

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service with multiple provider support"""
    
    def __init__(self):
        self.provider = getattr(settings, 'SMS_PROVIDER', 'console')
        self.setup_provider()
    
    def setup_provider(self):
        """Setup the SMS provider based on settings"""
        if self.provider == 'twilio':
            self.setup_twilio()
        elif self.provider == 'aws_sns':
            self.setup_aws_sns()
        elif self.provider == 'console':
            logger.info("Using console SMS provider for development")
        else:
            raise ImproperlyConfigured(f"Unknown SMS provider: {self.provider}")
    
    def setup_twilio(self):
        """Setup Twilio SMS provider"""
        try:
            from twilio.rest import Client
            
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
            
            if not all([account_sid, auth_token, from_number]):
                raise ImproperlyConfigured(
                    "Twilio requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER settings"
                )
            
            self.client = Client(account_sid, auth_token)
            self.from_number = from_number
            logger.info("Twilio SMS provider initialized successfully")
            
        except ImportError:
            raise ImproperlyConfigured(
                "Twilio provider requires 'twilio' package. Install with: pip install twilio"
            )
    
    def setup_aws_sns(self):
        """Setup AWS SNS SMS provider"""
        try:
            import boto3
            
            aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_region = getattr(settings, 'AWS_REGION', 'us-east-1')
            
            if aws_access_key and aws_secret_key:
                self.client = boto3.client(
                    'sns',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
            else:
                # Use default AWS credentials (IAM role, environment variables, etc.)
                self.client = boto3.client('sns', region_name=aws_region)
            
            logger.info("AWS SNS SMS provider initialized successfully")
            
        except ImportError:
            raise ImproperlyConfigured(
                "AWS SNS provider requires 'boto3' package. Install with: pip install boto3"
            )
    
    def validate_phone_number(self, phone_number):
        """Validate and format phone number (supports Indian numbers)"""
        if not phone_number:
            return False, "Phone number is required"

        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_number)

        # Handle Indian mobile numbers
        if cleaned.startswith('+91'):
            # Indian number with country code
            digits = cleaned[3:]  # Remove +91
            if len(digits) == 10 and digits[0] in '6789':
                return True, f"+91{digits}"
            else:
                return False, "Invalid Indian mobile number format"
        elif cleaned.startswith('91'):
            # Indian number with country code but no +
            digits = cleaned[2:]  # Remove 91
            if len(digits) == 10 and digits[0] in '6789':
                return True, f"+91{digits}"
            else:
                return False, "Invalid Indian mobile number format"
        elif len(cleaned) == 10 and cleaned[0] in '6789':
            # Indian number without country code
            return True, f"+91{cleaned}"
        elif re.match(r'^\+?1?\d{10}$', cleaned):
            # US/Canada number format (fallback)
            if not cleaned.startswith('+'):
                if cleaned.startswith('1') and len(cleaned) == 11:
                    cleaned = '+' + cleaned
                elif len(cleaned) == 10:
                    cleaned = '+1' + cleaned
                else:
                    cleaned = '+' + cleaned
            return True, cleaned
        else:
            return False, "Invalid phone number format. Please use Indian mobile number (+91 XXXXX XXXXX)"
    
    def send_sms(self, phone_number, message, sender_name="WallpaperHub"):
        """Send SMS message"""
        # Validate phone number
        is_valid, result = self.validate_phone_number(phone_number)
        if not is_valid:
            return False, result
        
        formatted_phone = result
        
        try:
            if self.provider == 'twilio':
                return self._send_twilio_sms(formatted_phone, message)
            elif self.provider == 'aws_sns':
                return self._send_aws_sns_sms(formatted_phone, message, sender_name)
            elif self.provider == 'console':
                return self._send_console_sms(formatted_phone, message)
            else:
                return False, f"Unknown SMS provider: {self.provider}"
                
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False, f"SMS sending failed: {str(e)}"
    
    def _send_twilio_sms(self, phone_number, message):
        """Send SMS via Twilio"""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone_number
            )
            
            logger.info(f"Twilio SMS sent successfully. SID: {message_obj.sid}")
            return True, f"SMS sent successfully. Message ID: {message_obj.sid}"
            
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return False, f"Twilio SMS failed: {str(e)}"
    
    def _send_aws_sns_sms(self, phone_number, message, sender_name):
        """Send SMS via AWS SNS"""
        try:
            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': sender_name
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"AWS SNS SMS sent successfully. Message ID: {message_id}")
            return True, f"SMS sent successfully. Message ID: {message_id}"
            
        except Exception as e:
            logger.error(f"AWS SNS SMS failed: {str(e)}")
            return False, f"AWS SNS SMS failed: {str(e)}"
    
    def _send_console_sms(self, phone_number, message):
        """Send SMS to console (development mode)"""
        print("\n" + "="*60)
        print("📱 SMS MESSAGE (DEVELOPMENT MODE)")
        print("="*60)
        print(f"To: {phone_number}")
        print(f"From: WallpaperHub")
        print(f"Message: {message}")
        print("="*60)
        print("Note: This is a development SMS. In production, this would be sent via SMS provider.")
        print("="*60 + "\n")
        
        logger.info(f"Console SMS sent to {phone_number}: {message}")
        return True, "SMS sent to console (development mode)"

# Global SMS service instance
sms_service = SMSService()

def send_otp_sms(phone_number, otp_code):
    """Send OTP SMS message"""
    message = f"""WallpaperHub Security Code

Your verification code is: {otp_code}

This code will expire in 10 minutes.
Do not share this code with anyone.

If you didn't request this code, please ignore this message.

- WallpaperHub Team"""
    
    return sms_service.send_sms(phone_number, message)

def send_password_reset_sms(phone_number, otp_code):
    """Send password reset SMS message"""
    message = f"""WallpaperHub Password Reset

Your password reset code is: {otp_code}

This code will expire in 10 minutes.
Do not share this code with anyone.

If you didn't request a password reset, please ignore this message.

- WallpaperHub Team"""
    
    return sms_service.send_sms(phone_number, message)

def send_welcome_sms(phone_number, username):
    """Send welcome SMS message"""
    message = f"""Welcome to WallpaperHub, {username}!

Your account has been created successfully.
Explore thousands of high-quality wallpapers at wallpaperhub.com

Thank you for joining our community!

- WallpaperHub Team"""
    
    return sms_service.send_sms(phone_number, message)
