"""Offline fixture adapter to the actual shared outer workflow. Never deployed."""
import json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from outer import run_outer
from watch import held_wait

def main():
    root=Path(sys.argv[1]);case=sys.argv[2]
    assert HERE/'raw/offline' in root.parents and root.resolve()==root
    def save(name,value):
        with (root/name).open('x') as stream:
            json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    if case=='watch':
        return held_wait([sys.executable,'-I','-B',str(HERE/'offline_entry.py'),str(root),'bad_gpu'],
                         save,root,os.environ.copy(),10)
    class Context:
        identity=lambda self,pid=None:{'pid':pid or os.getpid(),'offline_direct_child':True}
        record=staticmethod(save)
        def prepare(self):
            if case=='prepare_error':raise ValueError('controlled preparation failure')
            return .001 if case=='budget' else 5363.641942024231
        def commands(self):
            xml='<nvidia_smi_log><gpu><uuid>GPU-offline</uuid><minor_number>0</minor_number><gpu_recovery_action>None</gpu_recovery_action><compute_mode>Default</compute_mode><mig_mode><current_mig>Disabled</current_mig></mig_mode><remapped_rows><remapped_row_pending>No</remapped_row_pending><remapped_row_failure>No</remapped_row_failure></remapped_rows><utilization><gpu_util>100 %</gpu_util><memory_util>0 %</memory_util></utilization></gpu></nvidia_smi_log>'
            script="import sys;print("+repr(xml)+");print('raw stderr retained',file=sys.stderr);sys.exit("+('9' if case=='query_exit9' else '0')+")"
            return [[sys.executable,'-I','-B','-c',script]]
        def query(self,command):return subprocess.run(command,capture_output=True,text=True,timeout=2)
        def validate(self,records):
            if case=='bad_gpu':
                import importlib.util
                path=HERE.parents[0]/'batch-package/source/runtime-v1/resource_checks.py'
                # Import exact admitted stdlib validator, no ML/model side effects.
                sys.path.insert(0,str(path.parent));import common_guarded
                spec=importlib.util.spec_from_file_location('_actual_gpu_gate',path)
                gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
                gate.validate_idle_gpu(records[0]['stdout'],'','GPU-offline',0)
        def reconcile(self):pass
        def start_batch(self,deadline):
            (root/'batch-invoked').write_text('invoked')
            raise RuntimeError('controlled ambiguous launch')
    return run_outer(Context())

if __name__=='__main__':raise SystemExit(main())
