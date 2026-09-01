import logging

_logger = logging.getLogger(__name__)


def _attach_inherited_view(env, name, model, arch_xml, base_domain):
    """Create an ir.ui.view inheriting the first view matching base_domain,
    without ever hard-coding an external ID that may not exist/may differ
    across Odoo versions and customizations. Never raises: on any failure
    (base view not found, xpath not matching, ...) it just logs a warning
    and skips, so a UI nicety can never block module installation/upgrade.

    If the view was already attached by an earlier run, its arch is synced
    to the current definition on every call (same reasoning as
    _ph_fix_salary_rule_formulas: this module's data records aren't
    noupdate-refreshed by a plain upgrade once they already exist).
    """
    xmlid = f'ph_payroll_extension.{name}'
    existing = env.ref(xmlid, raise_if_not_found=False)
    if existing:
        if existing.arch_db != arch_xml:
            try:
                existing.sudo().write({'arch_db': arch_xml})
            except Exception:
                _logger.warning(
                    'ph_payroll_extension: failed to sync the "%s" UI '
                    'extension (model %s) to its latest definition.',
                    name, model, exc_info=True)
        return
    try:
        base_view = env['ir.ui.view'].search(base_domain, limit=1)
        if not base_view:
            _logger.warning(
                'ph_payroll_extension: could not find a base view for '
                'model %s (domain %s); skipping "%s" UI extension.',
                model, base_domain, name)
            return
        view = env['ir.ui.view'].create({
            'name': f'ph_payroll_extension.{name}',
            'type': base_view.type,
            'model': model,
            'inherit_id': base_view.id,
            'arch_db': arch_xml,
        })
        env['ir.model.data'].create({
            'name': name,
            'module': 'ph_payroll_extension',
            'model': 'ir.ui.view',
            'res_id': view.id,
            'noupdate': True,
        })
    except Exception:
        _logger.warning(
            'ph_payroll_extension: failed to attach the "%s" UI extension '
            '(model %s). The rest of the module still works; this is a '
            'display-only enhancement. See traceback below.',
            name, model, exc_info=True)


def _ph_input_code(code, negate=False):
    """Read an input's amount whether ``inputs`` is a plain dict (code ->
    amount, or code -> input-line record) or the classic wrapper object
    (dotted attribute access, 0.0 if missing).

    Uses bare ``except:`` clauses deliberately: this Odoo build's rule
    sandbox doesn't expose hasattr/getattr, NOR does it expose built-in
    exception classes like KeyError/AttributeError as names -- referencing
    them in an ``except (KeyError, ...):`` clause raises its own NameError
    the moment an exception actually needs to be matched. A bare except
    never needs to look up an exception class by name, so it works
    regardless of what this sandbox does or doesn't expose.
    """
    lines = [
        "try:",
        f"    _v = inputs[{code!r}]",
        "except:",
        "    try:",
        f"        _v = inputs.{code}",
        "    except:",
        "        _v = 0.0",
        "try:",
        "    result = _v.amount",
        "except:",
        "    result = _v or 0.0",
    ]
    if negate:
        lines.append("result = -result")
    return "\n".join(lines)


def _ph_category_sum(*codes):
    """Same idea as _ph_input_code but for ``categories``, which maps
    straight to totals (no .amount sub-attribute to unwrap). Each code is
    baked in as a literal attribute name at generation time (here in
    Python), so the generated rule code never needs a dynamic
    getattr(obj, variable_name) at execution time.
    """
    lines = []
    var_names = []
    for i, code in enumerate(codes):
        var = f"_c{i}"
        var_names.append(var)
        lines += [
            "try:",
            f"    {var} = categories[{code!r}]",
            "except:",
            "    try:",
            f"        {var} = categories.{code}",
            "    except:",
            f"        {var} = 0.0",
        ]
    terms = ' + '.join(f"({v} or 0.0)" for v in var_names)
    lines.append(f"result = {terms}")
    return "\n".join(lines)


_PH_SALARY_RULE_FORMULAS = {
    'ph_rule_basic': _ph_input_code('BASICWAGE'),
    'ph_rule_commission': _ph_input_code('COMMISSION'),
    'ph_rule_allow_taxable': _ph_input_code('ALLOWTAX'),
    'ph_rule_allow_nontaxable': _ph_input_code('ALLOWNONTAX'),
    'ph_rule_overtime': _ph_input_code('OVERTIME'),
    'ph_rule_gross': _ph_category_sum('PH_BASIC', 'PH_ALLOW', 'PH_OT'),
    'ph_rule_sss_ee': _ph_input_code('SSSEE', negate=True),
    'ph_rule_sss_er': _ph_input_code('SSSER'),
    'ph_rule_phic_ee': _ph_input_code('PHICEE', negate=True),
    'ph_rule_phic_er': _ph_input_code('PHICER'),
    'ph_rule_hdmf_ee': _ph_input_code('HDMFEE', negate=True),
    'ph_rule_hdmf_er': _ph_input_code('HDMFER'),
    'ph_rule_sss_loan': _ph_input_code('SSSLOAN', negate=True),
    'ph_rule_hdmf_loan': _ph_input_code('HDMFLOAN', negate=True),
    'ph_rule_company_loan': _ph_input_code('COMPANYLOAN', negate=True),
    'ph_rule_salary_advance': _ph_input_code('SALARYADV', negate=True),
    'ph_rule_net': _ph_category_sum('PH_GROSS', 'PH_SSS_EE', 'PH_PHIC_EE', 'PH_HDMF_EE', 'PH_LOANS'),
}

# Employer-share rules: informational only, kept out of the printed payslip
# but still visible in the backend Salary Computation tab.
_PH_SALARY_RULE_HIDE_ON_PAYSLIP = ('ph_rule_sss_er', 'ph_rule_phic_er', 'ph_rule_hdmf_er')


def _ph_fix_salary_rule_formulas(env):
    """Force-write the current salary rule formulas via the ORM, every time
    the module loads. Odoo's XML data loader protects already-existing
    noupdate records from being overwritten by a later module upgrade --
    that protection is keyed off a flag stored on the record's
    ir.model.data entry at the time it was first created, not off whatever
    the current file says, so simply editing the data file's noupdate
    attribute does not fix rules that already exist in an installed
    database. Writing the values directly here sidesteps that mechanism
    entirely and always wins.
    """
    for name, code in _PH_SALARY_RULE_FORMULAS.items():
        rule = env.ref(f'ph_payroll_extension.{name}', raise_if_not_found=False)
        if rule and rule.amount_python_compute != code:
            try:
                rule.sudo().write({'amount_python_compute': code})
            except Exception:
                _logger.warning(
                    'ph_payroll_extension: failed to force-sync the Python '
                    'code for salary rule %s.', name, exc_info=True)

    for name in _PH_SALARY_RULE_HIDE_ON_PAYSLIP:
        rule = env.ref(f'ph_payroll_extension.{name}', raise_if_not_found=False)
        if rule and rule.appears_on_payslip:
            try:
                rule.sudo().write({'appears_on_payslip': False})
            except Exception:
                _logger.warning(
                    'ph_payroll_extension: failed to hide salary rule %s '
                    'from the printed payslip.', name, exc_info=True)


def configure_ph_extension(env):
    """Attach menu, payslip UI, structure UI, contract UI and report
    addendum without hard-coding external IDs that may not exist (or may
    differ) in every Odoo Enterprise version/installation/customization.

    Called from both post_init_hook (fresh install) and _register_hook
    (every upgrade/server restart), so newly added UI attachments can
    self-heal on the next upgrade rather than requiring a clean reinstall.
    Every step is independently guarded/try-except'd, so a failure in one
    never blocks the others or the module itself.
    """
    # 0. Force-sync salary rule formulas (see _PH_SALARY_RULE_FORMULAS).
    _ph_fix_salary_rule_formulas(env)

    # 1. Reparent the PH Payroll Settings menu under the main Payroll app menu.
    ph_menu = env.ref('ph_payroll_extension.menu_ph_payroll_root', raise_if_not_found=False)
    if ph_menu and not ph_menu.parent_id:
        payroll_menu = env['ir.ui.menu'].search(
            [('name', '=', 'Payroll'), ('parent_id', '=', False)], limit=1)
        if payroll_menu:
            ph_menu.parent_id = payroll_menu.id

    # 2. Commission field + Allowances tab on the payslip form.
    _attach_inherited_view(
        env, 'view_hr_payslip_form_ph_inherit', 'hr.payslip',
        '<data>'
        '<xpath expr="//notebook" position="inside">'
        '<page string="Allowances" name="ph_allowances">'
        '<group>'
        '<group string="Commission">'
        '<field name="commission_amount"/>'
        '</group>'
        '<group string="Overtime">'
        '<field name="overtime_hours" readonly="1"/>'
        '</group>'
        '</group>'
        '<field name="allowance_line_ids">'
        '<list string="Allowances" editable="bottom">'
        '<field name="allowance_type_id"/>'
        '<field name="name"/>'
        '<field name="is_taxable"/>'
        '<field name="amount"/>'
        '</list>'
        '</field>'
        '<group class="oe_subtotal_footer oe_right">'
        '<field name="total_taxable_allowance"/>'
        '<field name="total_nontaxable_allowance"/>'
        '</group>'
        '</page>'
        '</xpath>'
        '</data>',
        [('model', '=', 'hr.payslip'), ('type', '=', 'form'), ('inherit_id', '=', False)],
    )

    # 3. PH Pay Policy tab on the Salary Structure form.
    _attach_inherited_view(
        env, 'view_hr_payroll_structure_form_ph_inherit', 'hr.payroll.structure',
        '<data>'
        '<xpath expr="//notebook" position="inside">'
        '<page string="PH Pay Policy" name="ph_pay_policy">'
        '<group>'
        '<group string="Pay Schedule">'
        '<field name="ph_pay_frequency"/>'
        '<field name="ph_deduction_cutoff" invisible="ph_pay_frequency == \'monthly\'"/>'
        '<field name="ph_cutoff_split_day" invisible="ph_pay_frequency == \'monthly\'"/>'
        '</group>'
        '<group string="Basic Pay &amp; Overtime">'
        '<field name="ph_pay_treatment"/>'
        '<field name="ph_standard_monthly_hours"/>'
        '</group>'
        '</group>'
        '</page>'
        '</xpath>'
        '</data>',
        [('model', '=', 'hr.payroll.structure'), ('type', '=', 'form'), ('inherit_id', '=', False)],
    )

    # 4. Recurring PH Allowances tab on the Contract (hr.version) form.
    _attach_inherited_view(
        env, 'view_hr_version_form_ph_inherit', 'hr.version',
        '<data>'
        '<xpath expr="//notebook" position="inside">'
        '<page string="PH Recurring Allowances" name="ph_recurring_allowances">'
        '<field name="ph_recurring_allowance_ids">'
        '<list string="Recurring Allowances" editable="bottom">'
        '<field name="allowance_type_id"/>'
        '<field name="is_taxable"/>'
        '<field name="amount"/>'
        '</list>'
        '</field>'
        '<p class="text-muted">These allowances will automatically be copied '
        'onto every new payslip generated for this contract. They can still '
        'be adjusted per payslip in the payslip\'s Allowances tab.</p>'
        '</page>'
        '</xpath>'
        '</data>',
        [('model', '=', 'hr.version'), ('type', '=', 'form'), ('inherit_id', '=', False)],
    )

    # 5. Allowance/loan breakdown addendum on the printed payslip report.
    addendum_template = env.ref(
        'ph_payroll_extension.ph_allowance_loan_breakdown', raise_if_not_found=False)
    base_report_template = None
    for candidate in ('hr_payroll.report_payslip_document', 'hr_payroll.report_payslip'):
        base_report_template = env.ref(candidate, raise_if_not_found=False)
        if base_report_template:
            break
    existing_inherit = env.ref(
        'ph_payroll_extension.report_payslip_document_ph_inherit', raise_if_not_found=False)
    if addendum_template and base_report_template and not existing_inherit:
        try:
            view = env['ir.ui.view'].create({
                'name': 'Payslip PH Allowance & Loan Breakdown',
                'type': 'qweb',
                'key': 'ph_payroll_extension.report_payslip_document_ph_inherit',
                'inherit_id': base_report_template.id,
                'arch_db': (
                    '<data>'
                    '<xpath expr="//div[hasclass(\'page\')]" position="inside">'
                    '<t t-call="ph_payroll_extension.ph_allowance_loan_breakdown"/>'
                    '</xpath>'
                    '</data>'
                ),
            })
            env['ir.model.data'].create({
                'name': 'report_payslip_document_ph_inherit',
                'module': 'ph_payroll_extension',
                'model': 'ir.ui.view',
                'res_id': view.id,
                'noupdate': True,
            })
        except Exception:
            _logger.warning(
                'ph_payroll_extension: failed to attach the payslip report '
                'addendum. The rest of the module still works; this only '
                'affects the printed PDF. See traceback below.', exc_info=True)
