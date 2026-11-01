"""Task-local correction after observed joblib semaphore side effect. No policy/Skill edits."""
from common_remote import ROOT,GPU_UUID,now,safe,sha,write_json
from common_remote import environment as original_environment

def environment():
    env=original_environment()
    env.update({'JOBLIB_MULTIPROCESSING':'0','JOBLIB_TEMP_FOLDER':str(ROOT/'tmp/joblib')})
    return env
