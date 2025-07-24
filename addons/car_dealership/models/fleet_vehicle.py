from odoo import models, fields, api, _

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    product_id = fields.Many2one('product.template', string='Dealership Vehicle')
    fleet_status = fields.Selection(related='product_id.state', string='Fleet Status', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order', help='Sale order associated with this vehicle')
    sale_status = fields.Selection(related='sale_id.state', string='Sale Status', store=True)
    sold_state_id = fields.Many2one('fleet.vehicle.state', compute='_compute_state_sold', store=True)

    @api.depends('sale_id.state')
    def _compute_state_sold(self):
        sold_state = self.env['fleet.vehicle.state'].search([('name', '=', 'Sold')], limit=1)
        for rec in self:
            if rec.sale_id and rec.sale_id.state == 'sale' and sold_state:
                rec.state_id = sold_state.id


    # def mark_as_sold(self):
    #     """Manual method to mark vehicle as sold"""
    #     sold_state = self.env['fleet.vehicle.state'].search([('name', '=', 'Sold')], limit=1)
    #     if sold_state:
    #         self.state_id = sold_state.id