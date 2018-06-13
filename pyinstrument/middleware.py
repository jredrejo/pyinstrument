from django.http import HttpResponse
from django.conf import settings
from pyinstrument import Profiler
from pyinstrument.profiler import NotMainThreadError
import time
import os
try:
	from django.utils.deprecation import MiddlewareMixin
except:
	import object as MiddlewareMixin

class ProfilerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        self.filter = getattr(settings, 'PYINSTRUMENT_FILTER', None)
        if self.filter:
            if self.filter not  in request.get_full_path():
                return
        self.profile_dir = getattr(settings, 'PYINSTRUMENT_PROFILE_DIR', None)

        if getattr(settings, 'PYINSTRUMENT_URL_ARGUMENT', 'profile') in request.GET or self.profile_dir:
            profiler = Profiler()
            profiler.start()

            request.profiler = profiler


    def process_response(self, request, response):
        if self.filter:
            if self.filter not  in request.get_full_path():
                return response
        if hasattr(request, 'profiler') or self.profile_dir:
            try:
                request.profiler.stop()

                output_html = request.profiler.output_html()
                if self.profile_dir:
                    filename = '{total_time:.3f}s {path} {timestamp:.0f}.html'.format(
                        total_time=request.profiler.root_frame().time(),
                        path=request.get_full_path().replace('/', '_'),
                        timestamp=time.time()
                    )

                    file_path = os.path.join(self.profile_dir, filename)

                    if not os.path.exists(self.profile_dir):
                        os.mkdir(self.profile_dir)

                    with open(file_path, 'w') as f:
                        f.write(output_html)

                if getattr(settings, 'PYINSTRUMENT_URL_ARGUMENT', 'profile') in request.GET:
                    return HttpResponse(output_html)
                else:
                    return response
            except NotMainThreadError:
                raise NotMainThreadError(not_main_thread_message)
        else:
            return response
