from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vehicle_id = fields.Many2one('product.template', string='Vehicle',
                                 help='Vehicle associated with this sale order')


    is_vehicle = fields.Boolean(related='vehicle_id.is_vehicle', string='is_vehicle', store=True)

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            for line in order.order_line:
                for lot in line.lot_ids:
                    self.env['fleet.vehicle'].mark_vehicle_as_sold_by_lot(lot.name, order)

        return res
