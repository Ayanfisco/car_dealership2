# fleet_vehicle.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    def mark_vehicle_as_sold_by_lot(self, lot_name, sale_order):
        """Find vehicle by license_plate and mark as Sold"""
        vehicle = self.search([('license_plate', '=', lot_name)], limit=1)
        if vehicle:
            sold_state = self.env['fleet.vehicle.state'].search([('name', '=', 'Sold')], limit=1)
            if sold_state:
                vehicle.write({
                    'state_id': sold_state.id,
                    'sale_id': sale_order.id,
                })
