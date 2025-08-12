from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingPopUp(models.Model):
    """Inherits stock.picking to enforce VIN/Chassis number entry
    for tracked products before validation.
    """
    _inherit = 'stock.picking'
    _description = 'Stock Picking'

    def button_validate(self):
        """Override the default validation to ensure a VIN/Chassis
        number is provided for tracked products.
        """
        for move in self.move_ids_without_package:
            product = move.product_id
            if product.tracking != 'none' and not move.move_line_ids:
                raise UserError(
                    _("You need to supply a VIN/Chasis Number for product:\n- %s") % product.display_name
                )
        return super().button_validate()
