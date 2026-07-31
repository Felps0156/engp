'''Core HTTP views.'''

from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    '''Return a database-independent liveness response.'''
    return HttpResponse('ok\n', content_type='text/plain')
