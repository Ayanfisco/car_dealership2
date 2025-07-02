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

    @api.model_create_multi
    def create(self, vals):
        """Override create to set up dealership vehicle properly"""
        if vals.get('is_dealership_vehicle'):
            vals['type'] = 'consu'  # Use 'type' instead of 'detailed_type' for Odoo 18
            vals['tracking'] = 'serial'  # Ensure tracking by serial number

            # Set category based on business type
            if vals.get('dealership_business_type'):
                category = self._get_dealership_category_by_type(vals['dealership_business_type'])
                if category:
                    vals['categ_id'] = category.id

        return super().create(vals)