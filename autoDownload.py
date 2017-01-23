#!/usr/bin/python3
# -*-coding:utf-8-*-

import os,sys
import urllib.parse,re,sqlite3

import xmlrpc.client

import logging

logging.basicConfig(format='[%(levelname)s]: %(message)s',level=logging.INFO)

# Aria2远程服务器相关设置
SERVER = 'http://localhost:6800/rpc'
SECRET = 'helscn'
DATABASE = '/home/helscn/.aria2/autoDownload.db'


# 查找超链接的规则列表，参数说明如下：
#   url         超链接地址
#   select      选择url网页的中超链接元素，使用jQuery语法，默认选择所有超链接
#   pattern     对选择的超链接文本使用正则表达式进一步筛选，默认匹配所有文本
#   target      超链接的目标保存路径，可以设为嵌套字典查找下级页面

DEFAULT_DIR='/home/helscn/下载'
kisssub_urls=['http://kisssub.org/sort-1-1.html','http://kisssub.org/sort-1-2.html','http://kisssub.org/sort-1-3.html']
rules=  [   {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*極影.*政宗君的復仇.*\[\d+\]',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/政宗君的复仇'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*澄空学园.*CHAOS.*CHILD.*第.*话.*MP4',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/ChaosChild/'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*動漫國.*人渣的本願.*\[\d+\]',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/人渣的本愿'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*動漫國.*廢天使加百列.*\[\d+\]',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/废天使加百列'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*動漫國字幕組.*為美好的世界獻上祝福.*\[\d+\]',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/为美好的世界献上祝福'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*極影字幕社.*幼女戰記\s+\d+.*MP4',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/幼女战记'
                         }
            },
            {
                'url':kisssub_urls,
                'select':'table#listTable tr td:eq(2) a',
                'pattern':r'.*澄空学园.*亚人酱有话要说.*第\d+话.*MP4',
                'target':{
                            'select':'a#magnet',
                            'target':'/home/helscn/视频/亚人酱有话说'
                         }
            }
        ]


def getit(values):
    '''循环迭代返回元素，如果只有一个元素则直接返回'''
    if type(values) in [list,tuple,set]:
        for v in values:
            yield v
    else:
        yield values 

def simplyify(s,length=37):
    '''简化长度过长的字符串'''
    s=str(s).strip()
    if len(s)>length:
        return s[:length]+'...'
    else:
        return s

cache={}
def fetchPage(url):
    '''通过URL来获取网页，增加缓存功能'''
    from pyquery import PyQuery
    global cache
    if url in cache:
        return cache[url]
    else:
        cache[url]=PyQuery(url)
        return cache[url]

def fetchURL(url=None,page=None,select=None,pattern=None,target=None):
    '''通过网页及选择表达式来获取超链接地址'''
    #newURLs=[]
    result=[]
    newTarget=None
    if type(url) in [list,tuple,set]:
        for u in url:
            logging.debug('正在搜索网页列表:{0}'.format(u))
            newResult=fetchURL(url=u,page=None,select=select,pattern=pattern,target=target)
            for r in newResult:
                if r not in result:
                    result.append(r)
        return result
    if page is None:
        if url:
            logging.debug('获取网页：{0}'.format(url))
            page=fetchPage(url)
    if not page:
        logging.error('缺少网页数据！')
        return
    else:
        logging.debug('正在搜索网页:{0}'.format(simplyify(page('title').text())))
    if not select:
        select='a'
    selections=page(select)
    if len(selections)==0:
        logging.debug('没有找到匹配的超链接！')
        return result
    else:
        logging.debug('通过[{0}]选择到{1}个候选元素'.format(select,len(selections)))
        for p in getit(pattern):
            if type(p) is not str:
                p = '.*'
            reg = re.compile(p)  # 编译目标超链接查找的正则表达式
            for node in selections:  # 遍历所有选择的节点
                nodeText = node.text.replace('\n', '').replace('\r', '')
                logging.debug('通过[{0}]查找文本：{1}'.format(p, nodeText))
                m = reg.match(nodeText)
                if m:  # 如果匹配表达式则保存链接地址
                    logging.info('通过正则表达式：{0}\n\t匹配到超链接：{1}'.format(p, simplyify(nodeText)))
                    u = node.get('href')
                    if type(target) is dict:
                        suburl=urllib.parse.urljoin(url,u)
                        logging.info('获取子页面:{0}'.format(suburl))
                        page=fetchPage(suburl)
                        newResult = fetchURL(url=suburl, page=page, select=target.get('select', None),
                                             pattern=target.get('pattern', None), target=target.get('target', None))
                        for r in newResult:
                            if r not in result:
                                result.append(r)
                    else:
                        if (target,u) not in result:
                            result.append((target,u))
        return result

def getConnection(database):
    isNewFile=False if os.path.isfile(database) else True
    conn=sqlite3.connect(database)
    if isNewFile:
        cursor=conn.cursor()
        cursor.execute('create table tasks (link text primary key,dir text,gid text)')
        cursor.close()
        conn.commit()
    return conn

def removeLink(conn,href):
    try:
        cursor=conn.cursor()
        cursor.execute('delete from tasks where link=?',(href,))
        conn.commit()
    except:
        logging.error('无法删除数据库中链接：{0}'.format(href))
    finally:
        cursor.close()

def addLink(conn,href,dir='',gid=''):
    try:
        cursor=conn.cursor()
        cursor.execute('insert into tasks values (?,?,?)',(href,dir,gid))
        conn.commit()
    except:
        logging.error('向数据库中插入链接出错：{0}'.format(href))
    finally:
        cursor.close()

def hasLink(conn,href):
    try:
        cursor=conn.cursor()
        cursor.execute('select link from tasks where link=?',(href,))
        if len(cursor.fetchall())>0:
            return True
    except:
        logging.error('向数据库中查询链接出现错误：{0}'.format(href))
    finally:
        cursor.close()
    return False

def showLinks(database):
    try:
        conn=getConnection(DATABASE)
        cursor=conn.cursor()
        for row in cursor.execute('select gid,dir,link from tasks'):
            print('{0[0]:20}{0[1]:20}{0[2]}'.format(row))
        if cursor.rowcount==0:
            print('数据库中没有历史下载记录！')
    except:
        logging.error('向数据库中查询链接出错！')
    finally:
        cursor.close()
        conn.close()

def clearLinks(database):
    try:
        conn=getConnection(DATABASE)
        cursor=conn.cursor()
        cursor.execute('delete from tasks')
        conn.commit()
    except:
        logging.error('清空数据库中链接出错！')
    finally:
        cursor.close()
        conn.close()

def sysAlert(title='',info='',icon='info',level='low'):
    os.system('notify-send -u "{level}" -i "{icon}" "{title}" "{info}"'.format(**locals()))

if __name__=='__main__':
    if len(sys.argv)>1:
        if sys.argv[1]=='list':
            showLinks(DATABASE)
        elif sys.argv[1]=='clear':
            clearLinks(DATABASE)
    else:
        conn=getConnection(DATABASE)
        s=xmlrpc.client.ServerProxy(SERVER)
        for rule in rules:
            result=fetchURL(**rule)
            for path,url in result:
                if not hasLink(conn,url):
                    try:
                        if not path:
                            logging.error('没有指定下载路径，使用默认路径:{1}'.format(path, DEFAULT_DIR))
                            path = DEFAULT_DIR
                        if not os.path.isdir(path):
                            logging.error('下载保存路径不存在：{0}'.format(path))
                            continue
                        gid=s.aria2.addUri('token:{0}'.format(SECRET),[url],{'dir':path})
                        addLink(conn,url,path,gid)
                    except:
                        logging.error('增加下载链接出错：{0}'.format(url))
                        sysAlert('添加下载任务出错',url,'error')
                    else:
                        logging.info('增加下载链接成功：{0}\n\t下载保存路径：{1}'.format(url,path))
                        sysAlert('增加下载任务：',url+'\n'+path,'info')
                else:
                    logging.info('下载链接已经存在：{0}'.format(url))
        conn.commit()
        conn.close()
