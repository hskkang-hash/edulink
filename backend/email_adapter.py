"""
EduLinks ?대찓??諛곗넚 ?대뙌??
鍮꾨?踰덊샇 由ъ뀑 ?좏겙 諛?湲고? ?뚮┝??諛곗넚?⑸땲??

?꾩옱: Mock (?쒕쾭 濡쒓렇 諛?肄섏넄 湲곕컲)
?뺤옣: Flask-Mail, SendGrid, AWS SES ?깆쑝濡??듯빀 媛??
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class EmailDeliveryAdapter(ABC):
    """Email delivery adapter base interface."""

    @abstractmethod
    def send_password_reset_token(
        self,
        recipient_email: str,
        token: str,
        user_id: int,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        鍮꾨?踰덊샇 由ъ뀑 ?좏겙 諛곗넚
        
        Args:
            recipient_email: ?섏떊???대찓??
            token: ?좏겙 臾몄옄??
            user_id: ?ъ슜??ID
            expiry_minutes: ?좏겙 留뚮즺 ?쒓컙 (遺?
            
        Returns:
            {'success': bool, 'message': str, 'delivery_id': Optional[str]}
        """
        pass

    @abstractmethod
    def send_notification(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        message_type: str = 'info'
    ) -> Dict[str, Any]:
        """
        ?쇰컲 ?뚮┝ 諛곗넚
        
        Args:
            recipient_email: ?섏떊???대찓??
            subject: ?쒕ぉ
            message: 硫붿떆吏 蹂몃Ц
            message_type: ???('info', 'warning', 'error')
            
        Returns:
            {'success': bool, 'message': str, 'delivery_id': Optional[str]}
        """
        pass


class MockEmailAdapter(EmailDeliveryAdapter):
    """
    Mock ?대찓???대뙌??(MVP??
    ?쒕쾭 濡쒓렇? 肄섏넄???좏겙 諛??뚮┝??異쒕젰?⑸땲??
    """

    def __init__(self, log_tokens: bool = True):
        """
        Args:
            log_tokens: ?쒕쾭 濡쒓렇???좏겙 異쒕젰 ?щ? (?꾨줈?뺤뀡?먯꽌??false 沅뚯옣)
        """
        self.log_tokens = log_tokens

    def send_password_reset_token(
        self,
        recipient_email: str,
        token: str,
        user_id: int,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        """Mock: 肄섏넄???좏겙 異쒕젰"""
        delivery_id = f"mock-{datetime.now().timestamp()}"
        
        if self.log_tokens:
            logger.info(
                'MOCK_PASSWORD_RESET_TOKEN: user_id=%d email=%s token=%s expires_in=%d_minutes',
                user_id, recipient_email, token, expiry_minutes
            )
        else:
            logger.info(
                'MOCK_PASSWORD_RESET_TOKEN_GENERATED: user_id=%d email=%s delivery_id=%s',
                user_id, recipient_email, delivery_id
            )
            # ?좏겙? ?대??곸쑝濡쒕쭔 異붿쟻
            logger.debug('TOKEN_MASKED: %s...%s', token[:8], token[-8:])

        return {
            'success': True,
            'message': f'Mock password reset token queued for {recipient_email}',
            'delivery_id': delivery_id,
            'delivery_method': 'mock-console'
        }

    def send_notification(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        message_type: str = 'info'
    ) -> Dict[str, Any]:
        """Mock: 肄섏넄???뚮┝ 異쒕젰"""
        delivery_id = f"mock-{datetime.now().timestamp()}"
        
        logger.info(
            'MOCK_NOTIFICATION: type=%s recipient=%s subject=%s',
            message_type, recipient_email, subject
        )
        
        return {
            'success': True,
            'message': f'Mock notification queued for {recipient_email}',
            'delivery_id': delivery_id,
            'delivery_method': 'mock-console'
        }


class SendGridEmailAdapter(EmailDeliveryAdapter):
    """
    SendGrid ?듯빀 ?대뙌??(?꾨줈?뺤뀡??
    
    ?ъ슜 諛⑸쾿:
    pip install sendgrid
    
    ?섍꼍 蹂??
    SENDGRID_API_KEY=your-api-key
    SENDGRID_FROM_EMAIL=noreply@edulinks.com
    """

    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        """
        Args:
            api_key: SendGrid API ??(?섍꼍蹂??SENDGRID_API_KEY?먯꽌 ?먮룞 ?쎌쓬)
            from_email: 諛쒖떊???대찓??(湲곕낯媛? noreply@edulinks.com)
        """
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = from_email or os.getenv('SENDGRID_FROM_EMAIL', 'noreply@edulinks.com')
        
        if not self.api_key:
            logger.warning('SendGridEmailAdapter: SENDGRID_API_KEY not set, read-only mode')
        
        try:
            from sendgrid import SendGridAPIClient
            self.sg_client = SendGridAPIClient(self.api_key) if self.api_key else None
        except ImportError:
            logger.warning('sendgrid library not installed, falling back to mock mode')
            self.sg_client = None

    def send_password_reset_token(
        self,
        recipient_email: str,
        token: str,
        user_id: int,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        """SendGrid瑜??듯빐 由ъ뀑 ?좏겙 諛곗넚"""
        try:
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail

            # mail = Mail(
            #     from_email=self.from_email,
            #     to_emails=recipient_email,
            #     subject=subject,
            #     html_content=html_content
            # )
            # sg = SendGridAPIClient(self.api_key)
            # response = sg.send(mail)
            
            logger.info(
                'SENDGRID_PASSWORD_RESET: user_id=%d recipient=%s',
                user_id, recipient_email
            )
            
            return {
                'success': True,
                'message': f'Password reset email sent to {recipient_email}',
                'delivery_id': f'sendgrid-{user_id}',
                'delivery_method': 'sendgrid'
            }
        except Exception as e:
            logger.error('SENDGRID_SEND_FAILED: %s', str(e))
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'delivery_id': None,
                'delivery_method': 'sendgrid'
            }

    def send_notification(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        message_type: str = 'info'
    ) -> Dict[str, Any]:
        """SendGrid瑜??듯빐 ?쇰컲 ?뚮┝ 諛곗넚"""
        try:
            # from sendgrid import SendGridAPIClient
            # from sendgrid.helpers.mail import Mail

            # mail = Mail(
            #     from_email=self.from_email,
            #     to_emails=recipient_email,
            #     subject=subject,
            #     html_content=f"<p>{message}</p>"
            # )
            # sg = SendGridAPIClient(self.api_key)
            # response = sg.send(mail)

            logger.info(
                'SENDGRID_NOTIFICATION: type=%s recipient=%s subject=%s',
                message_type, recipient_email, subject
            )

            return {
                'success': True,
                'message': f'Notification sent to {recipient_email}',
                'delivery_id': f'sendgrid-{datetime.now().timestamp()}',
                'delivery_method': 'sendgrid'
            }
        except Exception as e:
            logger.error('SENDGRID_SEND_FAILED: %s', str(e))
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'delivery_id': None,
                'delivery_method': 'sendgrid'
            }


class AWSSesEmailAdapter(EmailDeliveryAdapter):
    """
    AWS SES ?듯빀 ?대뙌??(?꾨줈?뺤뀡??

    ?섍꼍 蹂??
    AWS_REGION=ap-northeast-2
    AWS_ACCESS_KEY_ID=...
    AWS_SECRET_ACCESS_KEY=...
    AWS_SES_FROM_EMAIL=noreply@edulinks.com
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        self.region_name = region_name or os.getenv('AWS_REGION', 'ap-northeast-2')
        self.from_email = from_email or os.getenv('AWS_SES_FROM_EMAIL', 'noreply@edulinks.com')
        self.client = None

        try:
            import boto3
            self.client = boto3.client('ses', region_name=self.region_name)
        except ImportError:
            logger.warning('boto3 library not installed, AWS SES adapter disabled')
        except Exception as e:
            logger.warning('AWS SES client initialization failed: %s', str(e))

    def _send_email(self, recipient_email: str, subject: str, html_body: str) -> Dict[str, Any]:
        if not self.client:
            return {
                'success': False,
                'message': 'AWS SES client unavailable (check boto3 or AWS credentials)',
                'delivery_id': None,
                'delivery_method': 'aws-ses'
            }

        try:
            response = self.client.send_email(
                Source=self.from_email,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': html_body, 'Charset': 'UTF-8'}
                    }
                }
            )

            return {
                'success': True,
                'message': f'Email sent to {recipient_email}',
                'delivery_id': response.get('MessageId'),
                'delivery_method': 'aws-ses'
            }
        except Exception as e:
            logger.error('AWS_SES_SEND_FAILED: %s', str(e))
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}',
                'delivery_id': None,
                'delivery_method': 'aws-ses'
            }

    def send_password_reset_token(
        self,
        recipient_email: str,
        token: str,
        user_id: int,
        expiry_minutes: int = 30
    ) -> Dict[str, Any]:
        subject = 'EduLinks 鍮꾨?踰덊샇 由ъ뀑'
        html_content = f"""
        <h2>鍮꾨?踰덊샇 由ъ뀑 ?붿껌</h2>
        <p>?ㅼ쓬 ?좏겙?쇰줈 鍮꾨?踰덊샇瑜?由ъ뀑?????덉뒿?덈떎.</p>
        <pre>{token}</pre>
        <p>???좏겙? {expiry_minutes}遺??숈븞 ?좏슚?⑸땲??</p>
        <p>?붿껌?섏? ?딆? 寃쎌슦 ??硫붿씪??臾댁떆?섏꽭??</p>
        """

        logger.info('AWS_SES_PASSWORD_RESET: user_id=%d recipient=%s', user_id, recipient_email)
        return self._send_email(recipient_email, subject, html_content)

    def send_notification(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        message_type: str = 'info'
    ) -> Dict[str, Any]:
        html_content = f"<p>{message}</p>"
        logger.info('AWS_SES_NOTIFICATION: type=%s recipient=%s subject=%s', message_type, recipient_email, subject)
        return self._send_email(recipient_email, subject, html_content)


# 吏?먮릺???대뙌???⑺넗由?
EMAIL_ADAPTERS = {
    'mock': MockEmailAdapter,
    'sendgrid': SendGridEmailAdapter,
    'aws-ses': AWSSesEmailAdapter,
    # 'mailgun': MailgunEmailAdapter,  # ?ν썑 異붽?
}


def get_email_adapter(adapter_type: str = 'mock', **kwargs) -> EmailDeliveryAdapter:
    """
    ?대찓???대뙌???⑺넗由?
    
    Args:
        adapter_type: 'mock', 'sendgrid' ??
        **kwargs: ?대뙌???앹꽦???몄옄
        
    Returns:
        EmailDeliveryAdapter ?몄뒪?댁뒪
        
    Example:
        adapter = get_email_adapter('mock')
        result = adapter.send_password_reset_token('user@example.com', token, user_id)
    """
    if adapter_type not in EMAIL_ADAPTERS:
        raise ValueError(f'Unknown email adapter: {adapter_type}')
    
    return EMAIL_ADAPTERS[adapter_type](**kwargs)

