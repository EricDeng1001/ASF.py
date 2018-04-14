#coding:utf8
__author__ = 'Antinus'
__version__ = 0.1


import urllib2
import urllib
import re
from bs4 import BeautifulSoup
import urlparse

class UrlManager(object):
  def __init__( self ):
    self.new_urls = set()
    self.old_urls = set()

  def add_new_url( self , url ):
    if url is None or url is '':
      return None
    if url not in self.new_urls and url not in self.old_urls:
      self.new_urls.add( url )

  def add_new_urls( self , urls ):
    if urls is None or len( urls ) is 0:
      return None
    for url in urls:
      self.add_new_url( url )

  def has_new_url( self ):
    return len( self.new_urls ) is not 0

  def get_new_url( self ):
    url = self.new_urls.pop()
    self.old_urls.add( url )
    return url

class Downloader(object):
  def download( self , url ):
    if url is None or url == '':
      return None

    url = url.encode( 'utf-8' )
    userAgent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {
        'User-Agent': userAgent,
        'Referer': url
    }
    data = r""
    request = urllib2.Request( url , data , headers)
    response = urllib2.urlopen( request )
    if response.getcode() is not 200:
      return None
    content = response.read()
    return content

  def post( self , url , data ):
    data = urllib.urlencode( data )
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {
        'User-Agent': user_agent,
        'Referer': url
    }
    request = urllib2.Request( url , data , headers )
    print urllib2.urlopen( request ).read()


class HTMLParser:
  def __init__( self ):
    self.hrefRegExp = re.compile( r'https?://\w*' )
    self.dataRegDict = {
      "title": ( "title" , lambda s: s )
    }
    self.reType = type( re.compile( "1" ) )
    self.failedParse = 0

  def setDataParseRegExp( self , dataRegDict ):
    if type( dataRegDict ) is not dict:
      raise Exception("Type Error: dataRegDict must be a dict")
    self.dataRegDict = dataRegDict

  def setHrefRegExp( self , regExp ):
    if type( regExp ) is str:
      self.hrefRegExp = re.compile( regExp )
    elif type( regExp ) is self.reType:
      self.hrefRegExp = regExp
    else:
      raise Exception("Type error: setHrefRegExp must use a str or a compiled re.compile")

  def __get_new_urls( self , page_url , soup ):
    new_urls = set()
    links = soup.find_all( 'a' , href = self.hrefRegExp )
    for link in links:
      new_url = link['href']
      new_full_url = urlparse.urljoin( page_url , new_url )
      new_urls.add( new_full_url )
    return new_urls

  def __get_new_datas( self , page_url , soup ):
    res_datas = []
    for reg , callback in self.dataRegDict.items():
      partlyData = []
      nodes = soup.find_all( reg )
      if nodes:
        for node in nodes:
          resDict = callback( node )
          if resDict:
            partlyData.append( resDict )
        i = 0
        while i < len( partlyData ):
          if not res_datas:
            res_datas = partlyData
            break
          res_datas[i].update( partlyData[i] )
          i += 1
      else:
        self.failedParse += 1
        if self.failedParse > 20:
          print """
          has failed parse over %d pages, check if your regExp is right
          """ % self.failedParse
    return res_datas

  def parse( self , page_url , html_content ):
    if page_url == '' or html_content == '' or html_content is None:
      return None , None
    soup = BeautifulSoup( html_content , 'lxml' , from_encoding = 'utf-8' )
    new_urls = self.__get_new_urls( page_url , soup )
    new_datas = self.__get_new_datas( page_url , soup )
    return ( new_urls , new_datas )


class HTMLOutputer( object ):
  def __init__( self ):
    self.datas = list()
    self.outputFormat = {
        "title": "<p>%s</p>"
    }

  def collect_datas( self , datas ):
    if not datas:
      return None
    self.datas.extend( datas )
    print "collected %d new datas" % len( datas )
    return 0

  def setOutputFormat( self , outputFormat ):
    if type( outputFormat ) is not dict:
      raise Exception("Type Error: outputFormat must be a dict")
    self.outputFormat = outputFormat

  def output_html( self ):
    fout = open( 'output.html' , 'w' )
    fout.write("<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta charset='utf8'/>\n\t\t<title>python spider</title>\n\t</head>\n\t<body>")
    for data in self.datas:
      htmlSentence = ""
      for key in data.keys():
        try:
          htmlSentence += self.outputFormat[key] % ( data[key].encode('utf-8') )
        except KeyError as e:
          print e
      fout.write( htmlSentence )
    fout.write("\n\t</body>\n</html>")
    fout.close()

class Spider( object ):
  def __init__( self ):
    self.__urls = UrlManager()
    self.__downloader = Downloader()
    self.__parser = HTMLParser()
    self.__outputer = HTMLOutputer()

  def setSpider( self , hrefRegExp = None , dataRegDict = None, outputFormat = None ):
    if hrefRegExp is not None:
      self.__parser.setHrefRegExp( hrefRegExp )
    if dataRegDict is not None:
      self.__parser.setDataParseRegExp( dataRegDict )
    if outputFormat is not None:
      self.__outputer.setOutputFormat( outputFormat )

  def craw( self , root_url , maxCount ):
    count = 1
    self.__urls.add_new_url( root_url )

    while self.__urls.has_new_url():
      try:
        next_url = self.__urls.get_new_url()
        print 'craw %d : %s' % ( count , next_url )
        html_cont = self.__downloader.download( next_url )
        new_urls, new_datas = self.__parser.parse( next_url , html_cont )
        self.__urls.add_new_urls( new_urls )
        success = self.__outputer.collect_datas( new_datas )
        if success is not None:
          if count == maxCount:
              print '%d pages craw complete!' % ( count )
              break
          count += 1
      except urllib2.URLError as e:
        print 'craw failed , reason: %s' % ( e.reason )
      except Exception as  e:
        print "error:" , str( e )
    if count < maxCount:
     print "run out of url when not reaching the max count"
    self.__outputer.output_html()


  def post( self , url , data ):
    self.__downloader.post( url , data )

def downloadImg( root , node ):
  try:
    if node["src"][:4] != "http":
      return None
    return {
      "src": urlparse.urljoin( root , node["src"] )
      }
  except Exception as e:
    return None

if __name__  == "__main__":
  root_url = "https://image.baidu.com/search/index?tn=baiduimage&ipn=r&ct=201326592&cl=2&lm=-1&st=-1&fm=index&fr=&hs=0&xthttps=111111&sf=1&fmq=&pv=&ic=0&nc=1&z=&se=1&showtab=0&fb=0&width=&height=&face=0&istype=2&ie=utf-8&word=%E5%BC%A0%E5%AD%A6%E5%8F%8B&oq=%E5%BC%A0%E5%AD%A6%E5%8F%8B&rsp=-1"
  maxCount = 10
  objSpider = Spider()
  dataRegDict = {
    r"title": lambda node: {
      "title": node.get_text()
    },
    r"img": lambda node: downloadImg( root_url , node )
  }
  outputFormat = {
    "title": "<p>%s</p>",
    "src": "<img src='%s'></img>",
  }
  hrefRegExp = re.compile( r"https?://\w*" )
  objSpider.setSpider( dataRegDict = dataRegDict , outputFormat = outputFormat , hrefRegExp = hrefRegExp )
  objSpider.craw( root_url , maxCount );
