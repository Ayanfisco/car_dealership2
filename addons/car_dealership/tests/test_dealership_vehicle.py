from odoo.tests.common import TransactionCase

class TestDealershipVehicle(TransactionCase):
    def test_create_vehicle(self):
        vehicle = self.env['dealership.vehicle'].create({
            'name': 'Test Car',
            'vin_number': 'TESTVIN123456',
            'make_id': self.env.ref('fleet.model_brand_toyota').id,
            'model_id': self.env.ref('fleet.model_model_corolla').id,
            'year': 2024,
            'business_type': 'owner',
        })
        self.assertTrue(vehicle.id)

    def test_create_dealer_network_vehicle(self):
        partner = self.env['res.partner'].create({'name': 'Dealer Partner'})
        vehicle = self.env['dealership.vehicle'].create({
            'name': 'Dealer Car',
            'vin_number': 'VINDEALER123',
            'make_id': self.env.ref('fleet.model_brand_toyota').id,
            'model_id': self.env.ref('fleet.model_model_corolla').id,
            'year': 2023,
            'business_type': 'dealer_network',
            'vendor_id': partner.id,
            'commission_type': 'percentage',
            'commission_value': 5,
        })
        self.assertEqual(vehicle.business_type, 'dealer_network')
        self.assertEqual(vehicle.vendor_id, partner)

    def test_create_consigned_vehicle(self):
        partner = self.env['res.partner'].create({'name': 'Consignor Partner'})
        vehicle = self.env['dealership.vehicle'].create({
            'name': 'Consigned Car',
            'vin_number': 'VINCONSIGN123',
            'make_id': self.env.ref('fleet.model_brand_toyota').id,
            'model_id': self.env.ref('fleet.model_model_corolla').id,
            'year': 2022,
            'business_type': 'consigned',
            'vendor_id': partner.id,
            'commission_type': 'fixed',
            'commission_value': 500,
        })
        self.assertEqual(vehicle.business_type, 'consigned')
        self.assertEqual(vehicle.vendor_id, partner)

    def test_unique_vin_constraint(self):
        self.env['dealership.vehicle'].create({
            'name': 'Car1',
            'vin_number': 'VINUNIQUE123',
            'make_id': self.env.ref('fleet.model_brand_toyota').id,
            'model_id': self.env.ref('fleet.model_model_corolla').id,
            'year': 2025,
            'business_type': 'owner',
        })
        with self.assertRaises(Exception):
            self.env['dealership.vehicle'].create({
                'name': 'Car2',
                'vin_number': 'VINUNIQUE123',
                'make_id': self.env.ref('fleet.model_brand_toyota').id,
                'model_id': self.env.ref('fleet.model_model_corolla').id,
                'year': 2025,
                'business_type': 'owner',
            })
