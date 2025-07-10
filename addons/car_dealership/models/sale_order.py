from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    vehicle_id = fields.Many2one('product.template', string='Vehicle',
                                 help='Vehicle associated with this sale order')


    is_vehicle = fields.Boolean(related='vehicle_id.is_vehicle', string='is_vehicle', store=True)
