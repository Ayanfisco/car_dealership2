# Extend fleet.vehicle to create a dealership record when applicable
from odoo import models, api, _

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            # Optional condition: only create dealership vehicle for specific use cases
            if record.model_id:
                dealership_vehicle = self.env['dealership.vehicle'].create({
                    'model_id': record.model_id.id,
                    'make_id': record.model_id.brand_id.id,
                    'vin_number': record.vin_sn,
                    'color': record.color,
                    'year': record.model_year,
                    'mileage': record.odometer,
                    'fleet_category_id': record.category_id.id if record.category_id else False,
                    'transmission': record.transmission,
                    'fleet_vehicle_id': record.id,
                    # 'business_type': 'owner',  # or infer this dynamically
                    'purchase_price': record.car_value,
                })
                record.message_post(body=_("Dealership record created: %s" % dealership_vehicle.name))

        return records
