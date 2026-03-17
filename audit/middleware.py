# middleware.py
from audit.models import NavigationEvent

class NavigationTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        body_data = None
        try:
            body_data = request.body.decode('utf-8') if request.body else ''
        except Exception:
            body_data = 'unreadable body'

        response = self.get_response(request)

        if request.user.is_authenticated and not request.path.startswith('/static'):
            try:
                NavigationEvent.objects.create(
                    user=request.user,
                    url=request.path,
                    method=request.method,
                    payload=dict(request.POST) if request.method == "POST" else None,
                    headers=dict(request.headers),
                    parameters=body_data,
                    coming_from=request.META.get('HTTP_REFERER', 'untracked')
                )
            except Exception as e:
                print(f"Audit logging failed: {e}")

        return response