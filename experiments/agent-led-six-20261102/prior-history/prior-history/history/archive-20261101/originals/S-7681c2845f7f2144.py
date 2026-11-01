import datetime,json,os,socket,time,urllib.request
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
r=[]
for url in ['https://pypi.tuna.tsinghua.edu.cn/simple/pip/','https://mirrors.aliyun.com/pypi/simple/pip/']:
    start=time.monotonic()
    try:
        with urllib.request.urlopen(url,timeout=12) as res:data=res.read(65536);status=res.status
        r.append({'url':url,'status':status,'bytes':len(data),'seconds':time.monotonic()-start})
    except Exception as e:r.append({'url':url,'error':str(e),'seconds':time.monotonic()-start})
print(json.dumps(r))
