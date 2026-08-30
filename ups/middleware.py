from threading import Lock

from django.utils import timezone

from .retention import cleanup_expired_service_requests


_middleware_lock = Lock()
_last_cleanup_run = None


class ServiceRetentionCleanupMiddleware:

    cleanup_interval_seconds = 3600

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        self._run_cleanup_if_due()

        return self.get_response(request)

    def _run_cleanup_if_due(self):

        global _last_cleanup_run

        with _middleware_lock:
            now = timezone.now()

            if _last_cleanup_run and (now - _last_cleanup_run).total_seconds() < self.cleanup_interval_seconds:
                return

            cleanup_expired_service_requests()
            _last_cleanup_run = now
