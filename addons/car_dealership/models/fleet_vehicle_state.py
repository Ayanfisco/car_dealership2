from odoo import models, fields, api


class FleetVehicleState(models.Model):
    _inherit = 'fleet.vehicle.state'

    @api.model
    def _get_state_selections(self):
        # Get base selections first
        selections = super(FleetVehicleState, self)._get_state_selections()
        # Add our new state
        selections.append(('sold', 'Sold'))
        return selections

    def _valid_field_parameter(self, field, name):
        # Add 'tracking' to valid parameters
        return name == 'tracking' or super()._valid_field_parameter(field, name)
