from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Extends sale confirmation to update fleet vehicle states."""
        res = super().action_confirm()

        for order in self:
            for line in order.order_line:
                if line.product_id.detailed_type == 'vehicle':
                    # For Odoo 18, check lot_id first, then fall back to lot_ids
                    lot_name = line.lot_id.name if line.lot_id else (
                        line.lot_ids[0].name if line.lot_ids else None
                    )
                    if lot_name:
                        # Try to mark vehicle as sold
                        self.env['fleet.vehicle'].mark_vehicle_as_sold_by_lot(lot_name, order)
                        # Log the action in the chatter
                        msg = f"Vehicle with lot/serial number {lot_name} marked as sold."
                        order.message_post(body=msg)

        return res
