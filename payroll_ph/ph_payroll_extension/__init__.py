from . import models
from .models.ph_config import configure_ph_extension


def post_init_hook(env):
    """Kept as a belt-and-suspenders safety net for the moment right after a
    fresh install. The real, self-healing mechanism is
    HrPayslip._register_hook (models/hr_payslip.py), which calls the same
    configure_ph_extension function on every module upgrade and server
    restart too, not just on first install.
    """
    configure_ph_extension(env)
