# -*- coding: utf-8 -*-  
from django.http import HttpResponse  
from django.template import RequestContext, Template  
from django.views.decorators.csrf import csrf_exempt  
from django.utils.encoding import smart_str, smart_unicode 
import hashlib
 
 
TOKEN = "mytoken"
 
# to verify the API server          
def checkSignature(request):  
    global TOKEN  
    signature = request.GET.get("signature", None)
    timestamp = request.GET.get("timestamp", None)
    nonce = request.GET.get("nonce", None)
    echoStr = request.GET.get("echostr",None)
    token = TOKEN  
    tmpList = [token,timestamp,nonce]  
    tmpList.sort()  
    #tmpstr = "%s%s%s" % tuple(tmpList)  
    #tmpstr = hashlib.sha1(tmpstr).hexdigest()
    #if tmpstr == signature: 
    return HttpResponse(echoStr)
    #else:  
    #    return None