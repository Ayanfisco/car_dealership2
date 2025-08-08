from . import models

def check_sale_installed(cr, registry):
    from odoo.modules.module import module_installed
    from odoo.exceptions import UserError
    if not module_installed('sale'):
        raise UserError('The Sales module (sale) must be installed for Car Dealership to work.')