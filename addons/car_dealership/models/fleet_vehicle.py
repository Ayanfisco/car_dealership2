# Extend fleet.vehicle to create a dealership record when applicable
from odoo import models, fields, api, _

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    product_id = fields.Many2one('product.template', string='Dealership Vehicle')
    fleet_status = fields.Selection(related='product_id.state', string='Fleet Status', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order', help='Sale order associated with this vehicle')
    sale_status = fields.Selection(related='sale_id.state', string='Sale Status', store=True)

    @api.onchange('fleet_status')
    def _onchange_fleet_status(self):
        if self.sale_status == 'sale':
            self.state_id = 'sold'