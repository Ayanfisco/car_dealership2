
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging


class ProductTemplate(models.Model):
    """Extended product template for dealership vehicles"""
    _inherit = 'product.template'

    is_vehicle = fields.Boolean(
        'Is Vehicle', default=False)
