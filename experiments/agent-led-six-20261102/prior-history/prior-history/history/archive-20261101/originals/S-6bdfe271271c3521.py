"""Checkpoint/monitor contract; no training, forward or optimizer calls.

Pure metadata validation is testable without ML libraries. Real Tensor and
weights_only validation is a separate mandatory production completion step.
"""
import math

from adapter_common import generic

MONITORS = ('internal_validation_raw_mae', 'internal_validation_standardized_mse')


def need(value, reason):
    if not value:
        raise ValueError(reason)


def history_selection(cfg, history):
    monitor = cfg['monitor']
    need(monitor in MONITORS and isinstance(history, list) and len(history) > 0, 'monitor/history invalid')
    best, best_index = float('inf'), None
    previous_steps = 0
    for index, row in enumerate(history):
        need(type(row['epoch']) is int and row['epoch'] == index+1, 'epoch identity invalid')
        need(type(row['steps']) is int and row['steps'] > previous_steps, 'step identity invalid')
        previous_steps = row['steps']
        for key in MONITORS:
            need(type(row[key]) in (int, float) and math.isfinite(row[key]), 'nonfinite monitor column')
        need(row['monitor'] == monitor and row['monitor_key'] == monitor, 'history monitor mismatch')
        need(row['monitor_value'] == row[monitor], 'history monitor value mismatch')
        if row[monitor] < best-1e-7:
            best, best_index = row[monitor], index
    return best_index


def verify_metadata(cfg, history, best, last, state, config_sha, last_head_sha):
    best_index = history_selection(cfg, history)
    for tag, payload, index in (('best', best, best_index), ('last', last, len(history)-1)):
        row = history[index]
        need(payload['run_id'] == cfg['run_id'] and payload['task'] == cfg['task'], 'head run/task mismatch')
        need(payload['which'] == tag and payload['epoch_1_based'] == row['epoch']
             and payload['optimizer_steps'] == row['steps'], 'checkpoint epoch/steps mismatch')
        need(payload['config'] == cfg and payload['config_sha256'] == config_sha, 'checkpoint config mismatch')
        need(payload['encoder_sha256'] == cfg['pretrained_sha256'], 'checkpoint encoder mismatch')
        need(payload['head_config'] == cfg['head_config'] and payload['split_config'] == cfg['split_config'], 'head/split config mismatch')
        need(payload['monitor'] == cfg['monitor'] and payload['monitor_key'] == cfg['monitor'], 'checkpoint monitor mismatch')
        prefix = history[:index+1]
        best_value = float('inf')
        for item in prefix:
            if item[cfg['monitor']] < best_value-1e-7:
                best_value = item[cfg['monitor']]
        legacy_mse = min(item['internal_validation_standardized_mse'] for item in prefix)
        need(payload['best_monitor_value'] == best_value
             and payload['internal_validation_best_monitor_value'] == best_value, 'best monitor prefix mismatch')
        need(payload['monitor_value_at_checkpoint'] == row[cfg['monitor']], 'checkpoint current monitor mismatch')
        need(payload['best_internal_validation_standardized_mse'] == legacy_mse, 'legacy best-MSE semantic mismatch')
        need(payload['internal_validation_standardized_mse_at_checkpoint'] == row['internal_validation_standardized_mse'], 'checkpoint current-MSE mismatch')
    need(state['run_id'] == cfg['run_id'] and state['config'] == cfg
         and state['config_sha256'] == config_sha, 'training-state config mismatch')
    need(state['which'] == state['head_tag'] == 'last', 'training-state tag mismatch')
    need(state['epoch_1_based'] == last['epoch_1_based']
         and state['optimizer_steps'] == last['optimizer_steps'], 'training-state step mismatch')
    need(state['last_head_sha256'] == last_head_sha, 'training-state last-head hash mismatch')
    need(state['split_record_sha256'] == last['split_record_sha256'], 'training-state split mismatch')
    return {'monitor': cfg['monitor'], 'best_epoch': best_index+1,
            'best_steps': history[best_index]['steps'], 'last_epoch': len(history),
            'last_steps': history[-1]['steps'], 'legacy_MSE_and_selected_monitor_distinct': True}


def verify_optimizer_rng_tensors(cfg, last, state, torch):
    """Actual Tensor validation. Never use a stub to certify this function."""
    parameters = list(last['state_dict'].values())
    need(len(parameters) == 4 and all(isinstance(x, torch.Tensor) for x in parameters), 'head tensors missing')
    optimizer = state['optimizer']
    need(set(optimizer) == {'state', 'param_groups'} and len(optimizer['param_groups']) == 1, 'optimizer structure incomplete')
    group = optimizer['param_groups'][0]
    ids = group['params']
    need(len(ids) == 4 and len(set(ids)) == 4 and set(optimizer['state']) == set(ids), 'optimizer parameter identity incomplete')
    need(group['lr'] == cfg['head_config']['lr'] and group['weight_decay'] == cfg['head_config']['weight_decay'], 'optimizer hyperparameter drift')
    for parameter, index in zip(parameters, ids):
        values = optimizer['state'][index]
        need({'step', 'exp_avg', 'exp_avg_sq'} <= set(values), 'AdamW state tensor missing')
        for name in ('step', 'exp_avg', 'exp_avg_sq'):
            value = values[name]
            need(isinstance(value, torch.Tensor) and value.device.type == 'cpu'
                 and bool(torch.isfinite(value).all()), 'invalid optimizer tensor')
        need(values['step'].numel() == 1 and values['step'].item() == state['optimizer_steps'], 'optimizer tensor step mismatch')
        need(values['exp_avg'].shape == parameter.shape and values['exp_avg_sq'].shape == parameter.shape, 'optimizer tensor shape mismatch')
    rng = state['rng']
    need({'cpu_rng', 'torch_cpu', 'torch_cuda', 'sampler', 'sampler_device'} <= set(rng), 'RNG sources missing')
    need(isinstance(rng['cpu_rng'], dict) and len(rng['cpu_rng']) > 0 and rng['sampler_device'] == 'cpu', 'CPU/sampler RNG incomplete')
    need(isinstance(rng['torch_cuda'], list) and len(rng['torch_cuda']) == 1, 'single CUDA RNG missing')
    for value in [rng['torch_cpu'], rng['sampler'], *rng['torch_cuda']]:
        need(isinstance(value, torch.Tensor) and value.device.type == 'cpu'
             and value.dtype == torch.uint8 and value.numel() > 0, 'RNG Tensor missing or wrong dtype')
    return {'actual_tensor_state_checked': True, 'optimizer_parameters': 4, 'cuda_rng_sources': 1}


def verify_saved_checkpoints(root, cfg, evidence, torch):
    records = {}
    for name, file in (('best', 'caco2_wang-head-best.pt'), ('last', 'caco2_wang-head-last.pt'),
                        ('state', 'training-state-last.pt')):
        path = generic.safe(root, root/'artifacts'/file, True)
        records[name] = torch.load(path, map_location='cpu', weights_only=True)
    report = verify_metadata(cfg, evidence['history'], records['best'], records['last'], records['state'],
                             generic.sha(root/'source/config.json'), generic.sha(root/'artifacts/caco2_wang-head-last.pt'))
    need(report['best_epoch'] == evidence['best_epoch_1_based'], 'evidence best selection mismatch')
    report.update(verify_optimizer_rng_tensors(cfg, records['last'], records['state'], torch))
    return report
