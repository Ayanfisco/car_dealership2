from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DealershipVehicle(models.Model):
    """Extended vehicle model for dealership operations"""
    _name = 'dealership.vehicle'
    _description = 'Dealership Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char("name", tracking=True)
    make_id = fields.Many2one('fleet.vehicle.model.brand', string='Make', required=True)
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', required=True)
    quant_id = fields.Many2one('product.product', string='Stock Quant')
    quantity = fields.Integer('Quantity', default=1, tracking=True,
                              help="Number of vehicles of this make/model/year/color in stock.")

    available_quantity = fields.Float(related='quant_id.qty_available', string='Available Qty', store=True)
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')
    product_id2 = fields.Many2one('product.template', string='Product Template', ondelete='cascade')
    year = fields.Integer('Year', tracking=True)
    color = fields.Char('Color', tracking=True)
    engine_size = fields.Char('Engine Size', tracking=True, help="Engine size in liters or cc")
    mileage = fields.Float('Mileage (km)', tracking=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('returned', 'Returned')
    ], string='Status', default='available', tracking=True)