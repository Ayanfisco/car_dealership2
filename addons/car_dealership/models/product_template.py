
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging


class ProductTemplate(models.Model):
    """Extended product template for dealership vehicles"""
    _inherit = 'product.template'

    is_vehicle = fields.Boolean(
        'Is Vehicle', default=False)
    make_id = fields.Many2one(
        'fleet.vehicle.model.brand', string='Make', required=False)
    model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', required=False)
    year = fields.Integer(string='Year', required=False)
