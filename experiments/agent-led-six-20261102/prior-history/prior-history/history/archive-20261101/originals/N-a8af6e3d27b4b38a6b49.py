"""Future guarded preflight only: actual storage/RNG helpers, zero model updates."""
from adapter_common import generic


def run_storage_probe(module, root, path, cfg):
    torch = module.torch
    # Fixed Tensor payload tests serialization, not optimizer behavior/learning.
    tensor = torch.tensor([1.0, 2.0], dtype=torch.float32)
    generator = torch.Generator(device='cpu').manual_seed(cfg['head_config']['seed'])
    optimizer = {'state': {0: {'step': torch.tensor(0.0), 'exp_avg': torch.zeros_like(tensor),
                               'exp_avg_sq': torch.zeros_like(tensor)}},
                 'param_groups': [{'params': [0], 'lr': cfg['head_config']['lr'],
                                   'weight_decay': cfg['head_config']['weight_decay']}]}
    payload = {'run_id': cfg['run_id'], 'monitor': cfg['monitor'],
               'optimizer': module.optimizer_payload(optimizer),
               'rng': module.capture_training_rng(cfg['head_config']['seed'], generator),
               'parameter_updates': 0, 'purpose': 'synthetic_tensor_storage_only'}
    original = tensor.clone()
    torch.save(payload, generic.safe(root, path))
    restored = torch.load(generic.safe(root, path, True), map_location='cpu', weights_only=True)
    if not module.state_equal(payload, restored) or not torch.equal(tensor, original):
        raise ValueError('real optimizer/RNG Tensor serialization failed')
    return {'weights_only_load': True, 'full_payload_exact': True, 'actual_tensor_storage': True,
            'parameter_updates': 0, 'optimizer_state_origin': 'synthetic_tensor_payload_not_actual_learning',
            'path': str(path.relative_to(root)), 'sha256': generic.sha(path)}
