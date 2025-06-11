# SMS Service Setup Guide for WallpaperHub

This guide explains how to set up SMS functionality for user registration and password reset features in WallpaperHub.

## 📱 **SMS Features**

### **Registration Enhancement**
- ✅ **Phone number field** in signup form with validation
- ✅ **International format support** (+1 XXX XXX-XXXX)
- ✅ **Phone number verification** during signup
- ✅ **Welcome SMS** sent after successful registration
- ✅ **Duplicate phone number prevention**

### **Forgot Password Enhancement**
- ✅ **Email AND phone number** recovery options
- ✅ **SMS OTP delivery** for phone-based recovery
- ✅ **Same 3-step process** as email recovery
- ✅ **Professional UI/UX** matching WallpaperHub design
- ✅ **Rate limiting and security** features

## 🔧 **Development Setup (Current)**

Currently configured for **development mode** with console SMS output:

```python
# settings.py
SMS_PROVIDER = 'console'  # Development mode
```

**Console Output Example:**
```
📱 SMS MESSAGE (DEVELOPMENT MODE)
============================================================
To: +1 (555) 123-4567
From: WallpaperHub
Message: Your verification code is: 123456
============================================================
```

## 🚀 **Production Setup Options**

### **Option 1: Twilio (Recommended)**

#### **1. Install Twilio SDK**
```bash
pip install twilio
```

#### **2. Get Twilio Credentials**
1. Sign up at [twilio.com](https://www.twilio.com)
2. Get your Account SID and Auth Token
3. Purchase a phone number

#### **3. Update Settings**
```python
# settings.py
SMS_PROVIDER = 'twilio'
TWILIO_ACCOUNT_SID = 'your-account-sid'
TWILIO_AUTH_TOKEN = 'your-auth-token'
TWILIO_FROM_NUMBER = '+1234567890'  # Your Twilio phone number
```

#### **4. Environment Variables (Recommended)**
```bash
# .env file
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
```

```python
# settings.py
import os
SMS_PROVIDER = 'twilio'
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
```

### **Option 2: AWS SNS**

#### **1. Install Boto3**
```bash
pip install boto3
```

#### **2. Configure AWS Credentials**
```python
# settings.py
SMS_PROVIDER = 'aws_sns'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_REGION = 'us-east-1'
```

#### **3. Environment Variables**
```bash
# .env file
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

## 📋 **Database Models**

### **UserProfile Model**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=17, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    # ... other fields
```

### **PasswordResetOTP Model**
```python
class PasswordResetOTP(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone'),
    ]
    contact_value = models.CharField(max_length=255)
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES)
    otp_code = models.CharField(max_length=6)
    # ... other fields
```

## 🔐 **Security Features**

### **Phone Number Validation**
- ✅ **International format** validation
- ✅ **Automatic formatting** (+1 XXX XXX-XXXX)
- ✅ **Duplicate prevention** across users
- ✅ **Input sanitization** and normalization

### **OTP Security**
- ✅ **6-digit codes** with expiration (10 minutes)
- ✅ **Rate limiting** (max 5 attempts)
- ✅ **IP tracking** and user agent logging
- ✅ **Session management** for multi-step process

### **SMS Rate Limiting**
- ✅ **Resend cooldown** (60 seconds)
- ✅ **Daily limits** per phone number
- ✅ **Abuse prevention** mechanisms

## 🎨 **UI/UX Features**

### **Signup Form**
- ✅ **Name fields** (First Name, Last Name)
- ✅ **Phone number field** with formatting
- ✅ **Real-time validation** and feedback
- ✅ **Optional phone number** (not required)
- ✅ **Professional design** matching WallpaperHub theme

### **Forgot Password**
- ✅ **Email/Phone toggle** buttons
- ✅ **Dynamic input formatting** based on type
- ✅ **Progress indicators** for 3-step process
- ✅ **Masked contact display** for security
- ✅ **Responsive design** for all devices

## 🧪 **Testing**

### **Test Registration with Phone**
1. Go to `/signUpPage/`
2. Fill in name, email, phone number
3. Submit form
4. Check console for welcome SMS

### **Test Phone Password Reset**
1. Go to `/forgot-password/`
2. Click "Phone" button
3. Enter phone number: `+1 (555) 123-4567`
4. Check console for OTP SMS
5. Enter OTP and reset password

### **Test Email Password Reset**
1. Go to `/forgot-password/`
2. Click "Email" button (default)
3. Enter email address
4. Check console for OTP email
5. Complete reset process

## 📊 **Admin Interface**

### **UserProfile Admin**
- ✅ **Phone number management**
- ✅ **Verification status tracking**
- ✅ **Search by phone number**
- ✅ **Bulk operations** support

### **PasswordResetOTP Admin**
- ✅ **OTP tracking** (email and SMS)
- ✅ **Usage statistics**
- ✅ **Security monitoring**
- ✅ **Cleanup tools** for expired OTPs

## 🚨 **Production Checklist**

### **Before Going Live**
- [ ] Choose SMS provider (Twilio/AWS SNS)
- [ ] Set up production credentials
- [ ] Configure environment variables
- [ ] Test SMS delivery thoroughly
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Test international phone numbers
- [ ] Set up backup SMS provider (optional)

### **Security Considerations**
- [ ] Use HTTPS in production
- [ ] Secure SMS provider credentials
- [ ] Monitor for SMS abuse
- [ ] Implement phone number verification
- [ ] Set up fraud detection
- [ ] Regular security audits

## 💰 **Cost Considerations**

### **Twilio Pricing (Approximate)**
- **SMS**: $0.0075 per message (US)
- **Phone Number**: $1/month
- **International**: Varies by country

### **AWS SNS Pricing (Approximate)**
- **SMS**: $0.00645 per message (US)
- **International**: Varies by country
- **No monthly fees**

## 🔄 **Migration from Email-Only**

### **Backward Compatibility**
- ✅ **Existing email-based** password reset still works
- ✅ **No breaking changes** to current users
- ✅ **Gradual rollout** possible
- ✅ **Fallback to email** if SMS fails

### **User Migration**
1. **Existing users** can add phone numbers in profile
2. **New registrations** include phone number option
3. **Password reset** supports both methods
4. **Admin tools** for bulk phone number updates

## 📞 **Support and Troubleshooting**

### **Common Issues**
- **SMS not delivered**: Check provider credentials
- **Phone validation fails**: Verify international format
- **OTP expired**: Check expiration settings (10 minutes)
- **Rate limiting**: Check cooldown periods

### **Debugging**
- Enable Django logging for SMS service
- Check provider dashboards for delivery status
- Monitor database for OTP records
- Review console output in development

## 🎯 **Next Steps**

1. **Choose SMS provider** based on your needs
2. **Set up production credentials**
3. **Test thoroughly** with real phone numbers
4. **Deploy to staging** environment first
5. **Monitor and optimize** based on usage

---

**Need Help?** Check the SMS service logs or contact the development team for assistance with SMS setup and configuration.
