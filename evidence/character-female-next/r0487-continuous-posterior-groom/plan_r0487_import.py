from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def load_plan():
    """Import the runnable guide authoring script without running its entry point."""
    path = Path(__file__).with_name('plan-r0487.py')
    spec = spec_from_file_location('r0487_guide_authoring', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
