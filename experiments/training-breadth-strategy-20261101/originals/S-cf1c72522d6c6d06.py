"""Reviewed host transport. Same fixed Windows stream and pinned keys as Hainan Skill.
Credentials only decoded in memory. All local temporary/evidence paths are in this run.
This module is never uploaded to the target.
"""
import base64,datetime,hashlib,importlib.util,json,os,shlex,signal,subprocess,tempfile
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
WORKSPACE=RUN.parents[3]
SKILL=WORKSPACE/'rules/skills/hainan-compute-access/scripts/read_only.py'
spec=importlib.util.spec_from_file_location('registered_hainan_read_only',SKILL)
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

def remote(source,tag,*,payload=None,timeout=50):
    """Execute only operator-reviewed source; binary input is reserved for bounded uploads."""
    source=source if isinstance(source,str) else source.read_text()
    command='python3 -I -B -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(base64.b64encode(source.encode()).decode())+'))')
    secret=''
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record={'observed_at':stamp,'tag':tag,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'payload_bytes':len(payload) if payload is not None else 0,'timeout_seconds':timeout,'route':'Mac -> fixed Windows stdio TCP22 -> private-compute'}
    with (RUN/'raw/commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
    try:
        with tempfile.TemporaryDirectory(prefix='keys-',dir=RUN/'raw/local-tmp') as tmp:
            wf=Path(tmp)/'windows_known_hosts';wf.write_text(s.verified_key(s.WINDOWS_KNOWN_HOSTS.read_text(),'<GATEWAY_ADDRESS>',s.WINDOWS_FP)+'\n');wf.chmod(0o600)
            gateway=s.windows_ssh(wf)
            key_output,_=s.run(gateway+[s.windows_python(s.GET_TARGET_KEY)],'registered_target_key',timeout=15)
            tf=Path(tmp)/'target_known_hosts';tf.write_text(s.verified_key(json.loads(key_output)['known_hosts'],'<COMPUTE_ADDRESS>',s.TARGET_FP)+'\n');tf.chmod(0o600)
            decoded=subprocess.run(['/usr/bin/textutil','-convert','txt','-stdout',str(s.CREDENTIAL)],capture_output=True,timeout=10)
            if decoded.returncode:raise RuntimeError('Credential decode failed; content withheld')
            lines=[x.strip() for x in decoded.stdout.decode().splitlines() if x.strip()]
            if len(lines)!=1:raise RuntimeError('Credential structure changed; content withheld')
            secret=lines[0];env=os.environ.copy();env['SSHPASS']=secret
            args=['sshpass','-e','ssh','-T','-p','22','-o','ConnectTimeout=10','-o','ConnectionAttempts=1','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','HostKeyAlgorithms=ssh-ed25519','-o','UserKnownHostsFile='+str(tf),'-o','GlobalKnownHostsFile=/dev/null','-o','PreferredAuthentications=password','-o','PubkeyAuthentication=no','-o','NumberOfPasswordPrompts=1','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','-o','ForwardAgent=no','-o','ClearAllForwardings=yes','-o','PermitLocalCommand=no','-o','ControlMaster=no','-o','ControlPath=none','-o','SendEnv=-*','-o','ProxyCommand='+shlex.join(gateway+[s.windows_python(s.PROXY)]),'private-compute@<COMPUTE_ADDRESS>',command]
            p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
            try:out,err=p.communicate(payload,timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGTERM)
                try:out,err=p.communicate(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate()
                raise RuntimeError('Transport timeout; remote status unknown; query original job before retry') from None
            finally:env.pop('SSHPASS',None)
            out=out.replace(secret.encode(),b'[REDACTED]');err=err.replace(secret.encode(),b'[REDACTED]')
            (RUN/'raw'/f'{tag}.stderr').write_bytes(err)
            (RUN/'raw'/f'{tag}.stdout').write_bytes(out)
            with (RUN/'raw/commands.jsonl').open('a') as f:f.write(json.dumps({'tag':tag,'completed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'stdout_bytes':len(out),'stderr_bytes':len(err)})+'\n')
            if p.returncode:raise RuntimeError(f'{tag}: SSH/command exit {p.returncode}; evidence retained')
            return out
    except Exception as e:
        raise RuntimeError(str(e).replace(secret,'[REDACTED]') if secret else str(e)) from None
