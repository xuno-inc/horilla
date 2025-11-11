from django.db import connection
import threading

class CloseDBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Explicitly close the database connection after each request
        connection.close()
        return response


class ThreadDBConnectionMiddleware:
    """
    Middleware to ensure database connections are properly managed in threads.
    This helps prevent connection leaks in background threads.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.thread_local = threading.local()

    def __call__(self, request):
        # Store request in thread local for background threads
        self.thread_local.request = request
        try:
            response = self.get_response(request)
            return response
        finally:
            # Ensure connection is closed even if an exception occurs
            try:
                connection.close()
            except:
                pass
            # Clean up thread local
            if hasattr(self.thread_local, 'request'):
                delattr(self.thread_local, 'request')
