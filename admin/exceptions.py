from django.shortcuts import render_to_response

class pExcept(Exception):
        pass

class PlanetExceptionMiddleware:
	def process_exception(self, request, exception):
		if isinstance(exception, pExcept):
			return render_to_response('internal_error.html', {
				'msg': exception
			})
		return None
