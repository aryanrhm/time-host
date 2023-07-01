
from django.http import JsonResponse
import datetime
import socket

def timehost_view(request):
   current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   hostname = socket.gethostname()
   data = {
       'timestamp': current_time,
       'hostname': hostname
   }
   return JsonResponse(data)

