from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingPopUp(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Override the default validation to ensure a VIN/Chassis
        number is provided for tracked products.
        """
        for move in self.move_ids:
            product = move.product_id
            if product.tracking in ['serial', 'lot']:
                # Check if there are move lines with tracking info
                if not move.move_line_ids:
                    raise UserError(
                        _("You need to supply a VIN/Chassis Number for product:\n- %s") % product.display_name
                    )
                # Check each move line has lot/serial number (check both lot_id AND lot_name)
                for move_line in move.move_line_ids:
                    if not move_line.lot_id and not move_line.lot_name:
                        raise UserError(
                            _("You need to supply a VIN/Chassis Number for product:\n- %s") % product.display_name
                        )
        return super().button_validate()
