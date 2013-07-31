# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.template import RequestContext, Template
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str, smart_unicode

import xml.etree.ElementTree as ET
import urllib,urllib2,time,hashlib

TOKEN = "weixin"

YOUDAO_KEY = 871453612
YOUDAO_KEY_FROM = "unifamily"
YOUDAO_DOC_TYPE = "xml"

@csrf_exempt
def handleRequest(request):
	if request.method == 'GET':
		#response = HttpResponse(request.GET['echostr'],content_type="text/plain")
		response = HttpResponse(checkSignature(request),content_type="text/plain")
		return response
	elif request.method == 'POST':
		#c = RequestContext(request,{'result':responseMsg(request)})
		#t = Template('{{result}}')
		#response = HttpResponse(t.render(c),content_type="application/xml")
		response = HttpResponse(responseMsg(request),content_type="application/xml")
		return response
	else:
		return None

def checkSignature(request):
	global TOKEN
	signature = request.GET.get("signature", None)
	timestamp = request.GET.get("timestamp", None)
	nonce = request.GET.get("nonce", None)
	echoStr = request.GET.get("echostr",None)

	token = TOKEN
	tmpList = [token,timestamp,nonce]
	tmpList.sort()
	tmpstr = "%s%s%s" % tuple(tmpList)
	tmpstr = hashlib.sha1(tmpstr).hexdigest()
	if tmpstr == signature:
		return echoStr
	else:
		return None

def responseMsg(request):
	rawStr = smart_str(request.body)
	#rawStr = smart_str(request.POST['XML'])
	msg = paraseMsgXml(ET.fromstring(rawStr))
	
	queryStr = msg.get('Content','You have input nothing~')
	msgType = msg.get('MsgType', 'text')

	raw_youdaoURL = "http://fanyi.youdao.com/openapi.do?keyfrom=%s&key=%s&type=data&doctype=%s&version=1.1&q=" % (YOUDAO_KEY_FROM,YOUDAO_KEY,YOUDAO_DOC_TYPE)	
	
	event = msg.get('Event', '')

	if msgType == 'event':
		result = getBasicReply(msg, '欢迎使用，发送单词或者中文词语，将获得相应的解释;如果需要单词的读音，请在单词前面添加一个点，如.hello;欢迎推荐给你们de小伙伴们')

	elif queryStr.startswith('.'):
		queryStr = queryStr[1:]
		youdaoURL = "%s%s" % (raw_youdaoURL,urllib2.quote(queryStr))
		req = urllib2.Request(url=youdaoURL)
		result = urllib2.urlopen(req).read()
		replyContent = getPronounce(ET.fromstring(result))
		result = getReplyXml(msg,replyContent, queryStr)

	else:
		youdaoURL = "%s%s" % (raw_youdaoURL,urllib2.quote(queryStr))
		req = urllib2.Request(url=youdaoURL)
		result = urllib2.urlopen(req).read()
		replyContent = paraseYouDaoXml(ET.fromstring(result))
		result = getBasicReply(msg,replyContent)

	return result
		

def paraseMsgXml(rootElem):
	msg = {}
	if rootElem.tag == 'xml':
		for child in rootElem:
			msg[child.tag] = smart_str(child.text)
	return msg

def getPronounce(rootElem):
	replyContent = '';
	if rootElem.tag == 'youdao-fanyi':
		for child in rootElem:# 错误码
			if child.tag == 'errorCode':
				if child.text == '20':
					return 'too long to translate\n'
				elif child.text == '30':
					return 'can not be able to translate with effect\n'
				elif child.text == '40':
					return 'can not be able to support this language\n'
				elif child.text == '50':
					return 'invalid key\n'

			# 有道词典-基本词典
			elif child.tag == 'basic': 
				for c in child:
					if c.tag == 'phonetic':
						replyContent = '%s%s' % (replyContent, c.text)
	return replyContent


def paraseYouDaoXml(rootElem):
	replyContent = ''
	if rootElem.tag == 'youdao-fanyi':
		for child in rootElem:
			# 错误码
			if child.tag == 'errorCode':
				if child.text == '20':
					return 'too long to translate\n'
				elif child.text == '30':
					return 'can not be able to translate with effect\n'
				elif child.text == '40':
					return 'can not be able to support this language\n'
				elif child.text == '50':
					return 'invalid key\n'

			# 查询字符串
			elif child.tag == 'query':
				replyContent = "%s%s\n" % (replyContent, child.text)

			# 有道翻译
			elif child.tag == 'translation': 
				replyContent = '%s%s\n%s\n' % (replyContent, '-' * 3 + u'有道翻译' + '-' * 3, child[0].text)

			# 有道词典-基本词典
			elif child.tag == 'basic': 
				replyContent = "%s%s\n" % (replyContent, '-' * 3 + u'基本词典' + '-' * 3)
				for c in child:
					if c.tag == 'phonetic':
						replyContent = '%s%s\n' % (replyContent, c.text)
					elif c.tag == 'explains':
						for ex in c.findall('ex'):
							replyContent = '%s%s\n' % (replyContent, ex.text)

			# 有道词典-网络释义
			elif child.tag == 'web': 
				replyContent = "%s%s\n" % (replyContent, '-' * 3 + u'网络释义' + '-' * 3)
				for explain in child.findall('explain'):
					for key in explain.findall('key'):
						replyContent = '%s%s\n' % (replyContent, key.text)
					for value in explain.findall('value'):
						for ex in value.findall('ex'):
							replyContent = '%s%s\n' % (replyContent, ex.text)
					replyContent = '%s%s\n' % (replyContent,'--')
	return replyContent

def getBasicReply(msg,replyContent):
	extTpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[%s]]></MsgType><Content><![CDATA[%s]]></Content><FuncFlag>0</FuncFlag></xml>";
	extTpl = extTpl % (msg['FromUserName'],msg['ToUserName'],str(int(time.time())),'text',replyContent)
	return extTpl

def getReplyXml(msg,replyContent,queryStr):
	extTpl = "<xml><ToUserName><![CDATA[%s]]></ToUserName><FromUserName><![CDATA[%s]]></FromUserName><CreateTime>%s</CreateTime><MsgType><![CDATA[%s]]></MsgType><Music><Title><![CDATA[%s]]></Title><Description><![CDATA['%s']]></Description><MusicUrl><![CDATA[%s]]></MusicUrl><HQMusicUrl><![CDATA[%s]]></HQMusicUrl></Music><FuncFlag>0</FuncFlag></xml>";
	audioUrl = "http://dict.youdao.com/dictvoice?audio=%s"
	audioUrl = audioUrl % (queryStr)
	extTpl = extTpl % (msg['FromUserName'],msg['ToUserName'],str(int(time.time())),'music', queryStr, replyContent, audioUrl, audioUrl)

	return extTpl
