import logging
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth import get_user_model
import threading, traceback
# from notification.helpers import send_email_from_global_config
_user = threading.local()
_request = threading.local()
logger = logging.getLogger(__name__)
from django.views import debug  

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info("⚠️ Entered ErrorHandlingMiddleware")
        try:
            response = self.get_response(request)
            
            # Handle 404 responses
            if response.status_code == 404:
                logger.warning(f"404 Error: {request.path}")
                return render(request, 'errors/404.html', status=404)
            
            return response
        except Exception as e:
            logger.exception("Exception caught in middleware")
            return self.handle_exception(request, e)

    def process_exception(self, request, exception):
        logger.exception("✅ process_exception caught an error")
        return self.handle_exception(request, exception)
    
    def handle_exception(self, request, exception):

        # Get the full traceback
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        full_traceback = ''.join(tb_lines)
        
        # Capture user information
        user_info = "Anonymous User"
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"""
            Email: {request.user.email}
            Full Name: {request.user.get_full_name() if hasattr(request.user, 'get_full_name') else 'N/A'}
            """
        
        # Log it
        logger.error(f"Full traceback:\n{full_traceback}\n\nUser Info:\n{user_info}")
        
        User = get_user_model()
        try:
            superuser = User.objects.filter(is_superuser=True).first()
        except Exception:
            superuser = None
            
        # IP Address: {request.META.get('REMOTE_ADDR', 'Unknown')}
        
        if superuser and superuser.email:
            email_subject = "🚨 Unhandled Exception in Application"
            email_content = f"""
                A critical error occurred in the application.
                
                === USER INFORMATION ===
                {user_info}
                
                === REQUEST INFORMATION ===
                Path: {request.path}
                Method: {request.method}
                User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}
                
                
                === ERROR DETAILS ===
                Error Type: {type(exception).__name__}
                Error: {str(exception)}
                
                === FULL TRACEBACK ===
                {full_traceback}
                
                === REQUEST DATA ===
                GET: {dict(request.GET)}
                POST: {dict(request.POST)}
                
                Please investigate immediately.
            """
            # send_email_from_global_config(email_subject, superuser, email_content)
        
        context = {
            "message": "An unexpected error occurred. Our team has been notified.",
            "request_path": request.path,
            "error": str(exception)
        }
        
        return render(request, "errors/500.html", context=context, status=500)
        
    


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        response = self.get_response(request)
        return response
    
class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request.value = request
        response = self.get_response(request)
        return response

def get_current_user():
    settings.LOGGER.info("⚠️ get_current_user called")
    return getattr(_user, 'value', None)

def get_current_request():
    """Get current request from thread-local storage"""
    request = getattr(_request, 'value', None)
    settings.LOGGER.info(f"🔍 Retrieving current request: {request}")
    return request