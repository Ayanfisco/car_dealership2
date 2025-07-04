from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    """Extended product template for dealership vehicles"""
    _inherit = 'product.template'

    # Dealership specific fields
    is_dealership_vehicle = fields.Boolean('Is Dealership Vehicle', default=False)
    dealership_business_type = fields.Selection([
        ('owner', 'Owner Product'),
        ('dealer_network', 'Dealer Network Product'),
        ('consigned', 'Consigned Product')
    ], string='Dealership Business Type')
    vehicle_make_id = fields.Many2one('fleet.vehicle.model.brand', string='Vehicle Make')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', string='Vehicle Model')
    default_commission_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ], string='Default Commission Type')
    default_commission_value = fields.Float('Default Commission Value')
    default_vendor_id = fields.Many2one('res.partner', string='Default Vendor/Consignor',
                                        help="Default dealer or consignor for this product type")
    is_vehicle = fields.Boolean('Is Vehicle', default=False, help="Check if this product is a vehicle. If checked, a record will be created in both Fleet and Car Dealership modules.")

    @api.onchange('is_dealership_vehicle')
    def _onchange_is_dealership_vehicle(self):
        if self.is_dealership_vehicle:
            # Set default values for dealership vehicles
            self.type = 'consu'  # Use 'type' instead of 'detailed_type' for Odoo 18
            self.tracking = 'serial'  # Track by unique serial number (VIN)
            self.categ_id = self._get_default_dealership_category()
        else:
            self.dealership_business_type = False
            self.vehicle_make_id = False
            self.vehicle_model_id = False

    @api.onchange('dealership_business_type')
    def _onchange_dealership_business_type(self):
        if self.dealership_business_type:
            category = self._get_dealership_category_by_type(self.dealership_business_type)
            if category:
                self.categ_id = category.id

    @api.onchange('vehicle_make_id')
    def _onchange_vehicle_make_id(self):
        if self.vehicle_make_id:
            return {'domain': {'vehicle_model_id': [('brand_id', '=', self.vehicle_make_id.id)]}}
        return {'domain': {'vehicle_model_id': []}}

    @api.onchange('vehicle_model_id')
    def _onchange_vehicle_model_id(self):
        if self.vehicle_model_id and self.vehicle_make_id:
            # Auto-generate product name
            self.name = f"{self.vehicle_make_id.name} {self.vehicle_model_id.name}"

    def _get_default_dealership_category(self):
        """Get default product category for dealership vehicles"""
        category = self.env['product.category'].search([
            ('name', '=', 'Dealership Vehicles')
        ], limit=1)
        return category

    def _get_dealership_category_by_type(self, business_type):
        """Get product category based on business type"""
        category_mapping = {
            'owner': 'Owner Products',
            'dealer_network': 'Dealer Network Products',
            'consigned': 'Consigned Products'
        }
        category_name = category_mapping.get(business_type)
        if category_name:
            return self.env['product.category'].search([
                ('name', '=', category_name)
            ], limit=1)
        return False

    @api.model
    def create(self, vals):
        if vals.get('is_vehicle'):
            vals['type'] = 'product'  # Make it storable
            vals['tracking'] = 'serial'  # Enable serial tracking
            # Check for existing product with same make, model, and year
            domain = [
                ('is_vehicle', '=', True),
                ('vehicle_make_id', '=', vals.get('vehicle_make_id')),
                ('vehicle_model_id', '=', vals.get('vehicle_model_id')),
                ('year', '=', vals.get('year'))
            ]
            existing = self.env['product.template'].search(domain, limit=1)
            if existing:
                # Increase inventory for existing product
                stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
                if stock_location:
                    self.env['stock.quant'].create({
                        'product_id': existing.id,
                        'location_id': stock_location.id,
                        'quantity': 1.0,
                        'inventory_quantity': 1.0,
                    })
                return existing
        product = super().create(vals)
        if vals.get('is_vehicle'):
            # Create Fleet Vehicle
            fleet_vals = {
                'model_id': vals.get('vehicle_model_id'),
                'brand_id': vals.get('vehicle_make_id'),
                'license_plate': product.name,
            }
            fleet_vehicle = self.env['fleet.vehicle'].create(fleet_vals)
            # Create Dealership Vehicle
            dealership_vals = {
                'name': product.name,
                'make_id': vals.get('vehicle_make_id'),
                'model_id': vals.get('vehicle_model_id'),
                'product_id': product.id,
                'fleet_vehicle_id': fleet_vehicle.id,
                'business_type': vals.get('dealership_business_type') or 'owner',
            }
            self.env['dealership.vehicle'].create(dealership_vals)
            # Create incoming stock move for inventory
            stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
            if stock_location:
                self.env['stock.quant'].create({
                    'product_id': product.id,
                    'location_id': stock_location.id,
                    'quantity': 1.0,
                    'inventory_quantity': 1.0,
                })
        return product

    def write(self, vals):
        res = super().write(vals)
        for product in self:
            if vals.get('is_vehicle') and not self.env['dealership.vehicle'].search([('product_id', '=', product.id)]):
                product.type = 'product'
                product.tracking = 'serial'
                # Create Fleet Vehicle if not exists
                fleet_vals = {
                    'model_id': product.vehicle_model_id.id,
                    'brand_id': product.vehicle_make_id.id,
                    'license_plate': product.name,
                }
                fleet_vehicle = self.env['fleet.vehicle'].create(fleet_vals)
                # Create Dealership Vehicle if not exists
                dealership_vals = {
                    'name': product.name,
                    'make_id': product.vehicle_make_id.id,
                    'model_id': product.vehicle_model_id.id,
                    'product_id': product.id,
                    'fleet_vehicle_id': fleet_vehicle.id,
                    'business_type': product.dealership_business_type or 'owner',
                }
                self.env['dealership.vehicle'].create(dealership_vals)
                # Create incoming stock move for inventory
                stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
                if stock_location:
                    self.env['stock.quant'].create({
                        'product_id': product.id,
                        'location_id': stock_location.id,
                        'quantity': 1.0,
                        'inventory_quantity': 1.0,
                    })
        return res