import datetime,json,os,socket,time,urllib.request
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
path='/packages/e5/35/0c52d708144c2deb595cd22819a609f78fdd699b95ff6f0ebcd456e3c7c1/torch-2.6.0-cp312-cp312-manylinux1_x86_64.whl'
r=[]
for prefix in ['https://pypi.tuna.tsinghua.edu.cn','https://mirrors.aliyun.com/pypi']:
    url=prefix+path;start=time.monotonic()
    try:
        req=urllib.request.Request(url,headers={'Range':'bytes=0-4194303'})
        with urllib.request.urlopen(req,timeout=12) as res:data=res.read(4*1024**2);status=res.status;final=res.url;headers=dict(res.headers)
        r.append({'url':url,'status':status,'final_url':final,'bytes':len(data),'seconds':time.monotonic()-start,'content_range':headers.get('Content-Range'),'content_length':headers.get('Content-Length')})
    except Exception as e:r.append({'url':url,'error':str(e),'seconds':time.monotonic()-start})
print(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bounded_download_samples':r}))
