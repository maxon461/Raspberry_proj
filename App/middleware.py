from django.http import HttpResponse

class MimeTypeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Set correct MIME types for static files
        if request.path.endswith('.js'):
            response['Content-Type'] = 'application/javascript'
        elif request.path.endswith('.css'):
            response['Content-Type'] = 'text/css'
        elif request.path.endswith('.json'):
            response['Content-Type'] = 'application/json'
        
        return response
