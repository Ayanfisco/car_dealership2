from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

logger = logging.getLogger(__name__)

class DealershipVehicle(models.Model):
    """Extended vehicle model for dealership operations"""
    _name = 'dealership.vehicle'
    _description = 'Dealership Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    name = fields.Char("name", tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user, tracking=True)
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
    
    # Dashboard computed fields
    total_available_vehicles = fields.Integer('Total Available Vehicles', compute='_compute_dashboard_stats', store=False)
    total_sold_vehicles = fields.Integer('Total Sold Vehicles', compute='_compute_dashboard_stats', store=False)
    total_reserved_vehicles = fields.Integer('Total Reserved Vehicles', compute='_compute_dashboard_stats', store=False)
    
    # Additional fields for better dashboard display
    vin_number = fields.Char('VIN Number', tracking=True, help="Vehicle Identification Number")
    purchase_price = fields.Monetary('Purchase Price', currency_field='currency_id', tracking=True)
    selling_price = fields.Monetary('Selling Price', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    business_type = fields.Selection([
        ('owner', 'Owner Product'),
        ('dealer_network', 'Dealer Network Product'),
        ('consigned', 'Consigned Product')
    ], string='Business Type', required=True, default='owner', tracking=True)

    # Website fields
    website_published = fields.Boolean('Published on Website', default=False, copy=False)
    website_description = fields.Html('Website Description', sanitize_attributes=False, translate=True)
    website_meta_title = fields.Char("Website meta title", translate=True)
    website_meta_description = fields.Text("Website meta description", translate=True)
    website_meta_keywords = fields.Char("Website meta keywords", translate=True)
    website_meta_og_img = fields.Char("Website opengraph image")
    website_sequence = fields.Integer('Website Sequence', default=10, help='Display order on website')

    # Computed fields for vehicle inventory totals
    product_id = fields.Many2one('product.product', string='Product', required=True)
    available = fields.Float(related='product_id.qty_available', string='Available Stock')
    total_vehicles_available = fields.Float(
        string='Total Available Vehicles',
        compute='_compute_vehicle_inventory',
        help='Total quantity of available vehicle products in inventory'
    )

    total_vehicles_reserved = fields.Float(
        string='Total Reserved Vehicles',
        compute='_compute_vehicle_inventory',
        help='Total quantity of reserved vehicle products in inventory'
    )

    total_vehicles_on_hand = fields.Float(
        string='Total Vehicles On Hand',
        compute='_compute_vehicle_inventory',
        help='Total quantity on hand of vehicle products in inventory'
    )

    def _compute_vehicle_inventory(self):
        """
        Compute the total available and reserved quantities for all vehicle products
        Compatible with Odoo 18
        """
        # Get all product templates marked as vehicles
        vehicle_products = self.env['product.template'].search([
            ('is_vehicle', '=', True)
        ])

        if not vehicle_products:
            # If no vehicle products found, set all values to 0
            for record in self:
                record.total_vehicles_available = 0.0
                record.total_vehicles_reserved = 0.0
                record.total_vehicles_on_hand = 0.0
            return

        # Get all product variants from these templates
        vehicle_variants = self.env['product.product'].search([
            ('product_tmpl_id', 'in', vehicle_products.ids)
        ])

        # Initialize totals
        total_available = 0.0
        total_reserved = 0.0
        total_on_hand = 0.0

        # Calculate totals using stock quants directly (more reliable)
        for product in vehicle_variants:
            # Get stock quants for this product in internal locations
            quants = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'internal')
            ])

            for quant in quants:
                total_on_hand += quant.quantity
                total_reserved += quant.reserved_quantity

        total_available = total_on_hand - total_reserved

        # Set the same values for all records since this is global inventory data
        for record in self:
            record.total_vehicles_available = total_available
            record.total_vehicles_reserved = total_reserved
            record.total_vehicles_on_hand = total_on_hand

    # Alternative method using direct SQL query for better performance with large datasets
    def _compute_vehicle_inventory_sql(self):
        """
        Alternative computation method using SQL for better performance
        """
        # SQL query to get totals directly from stock_quant table
        query = """
            SELECT 
                COALESCE(SUM(sq.quantity), 0) as total_on_hand,
                COALESCE(SUM(sq.reserved_quantity), 0) as total_reserved
            FROM stock_quant sq
            JOIN product_product pp ON sq.product_id = pp.id
            JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE pt.is_vehicle = true
            AND sq.location_id IN (
                SELECT id FROM stock_location 
                WHERE usage = 'internal'
            )
        """

        self.env.cr.execute(query)
        result = self.env.cr.fetchone()

        if result:
            total_on_hand = result[0] or 0.0
            total_reserved = result[1] or 0.0
            total_available = total_on_hand - total_reserved
        else:
            total_on_hand = total_reserved = total_available = 0.0

        for record in self:
            record.total_vehicles_available = total_available
            record.total_vehicles_reserved = total_reserved
            record.total_vehicles_on_hand = total_on_hand
    @api.depends('state')
    def _compute_dashboard_stats(self):
        """Compute dashboard statistics for all vehicles"""
        for record in self:
            # Get counts from product.template where is_vehicle=True
            available_count = self.env['product.template'].search_count([
                ('is_vehicle', '=', True),
                ('state', '=', 'available')
            ])
            
            sold_count = self.env['product.template'].search_count([
                ('is_vehicle', '=', True),
                ('state', '=', 'sold')
            ])
            
            reserved_count = self.env['product.template'].search_count([
                ('is_vehicle', '=', True),
                ('state', '=', 'reserved')
            ])
            
            # Alternative: Count from dealership.vehicle records
            # This gives more accurate counts for the dashboard
            dealership_available = self.env['dealership.vehicle'].search_count([
                ('state', '=', 'available')
            ])
            
            dealership_sold = self.env['dealership.vehicle'].search_count([
                ('state', '=', 'sold')
            ])
            
            dealership_reserved = self.env['dealership.vehicle'].search_count([
                ('state', '=', 'reserved')
            ])
            
            record.total_available_vehicles = dealership_available
            record.total_sold_vehicles = dealership_sold
            record.total_reserved_vehicles = dealership_reserved
    
    @api.model
    def get_dashboard_data(self):
        """Get dashboard data for use in kanban view"""
        available_vehicles = self.search([('state', '=', 'available')])
        sold_vehicles = self.search([('state', '=', 'sold')])
        reserved_vehicles = self.search([('state', '=', 'reserved')])
        
        # Calculate total quantities
        available_qty = sum(vehicle.available_quantity or vehicle.quantity for vehicle in available_vehicles)
        sold_qty = len(sold_vehicles)  # Count of sold vehicles
        reserved_qty = sum(vehicle.quantity for vehicle in reserved_vehicles)
        
        return {
            'available_count': len(available_vehicles),
            'sold_count': sold_qty,
            'reserved_count': len(reserved_vehicles),
            'available_quantity': available_qty,
            'total_vehicles': len(available_vehicles) + sold_qty + len(reserved_vehicles)
        }
    
    def action_mark_sold(self):
        """Action to mark vehicle as sold"""
        for record in self:
            record.state = 'sold'
            # Update related product state if needed
            if record.product_id2:
                record.product_id2.state = 'sold'
        return True
    
    def action_mark_available(self):
        """Action to mark vehicle as available"""
        for record in self:
            record.state = 'available'
            if record.product_id2:
                record.product_id2.state = 'available'
        return True
    
    def action_view_details(self):
        """Action to view vehicle details"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle Details',
            'res_model': 'dealership.vehicle',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_vehicle_report(self):
        """Action to generate vehicle report"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'dealership.vehicle_report',
            'report_type': 'qweb-pdf',
            'context': {'active_ids': self.ids}
        }
    
    def action_inventory_report(self):
        """Action to view inventory report"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Report',
            'res_model': 'dealership.vehicle',
            'view_mode': 'pivot,graph',
            'domain': [('id', 'in', self.ids)],
            'context': {
                'group_by': ['make_id', 'model_id', 'state'],
                'search_default_available': 1
            }
        }
    
    @api.model
    def create(self, vals):
        """Override create to ensure proper vehicle setup"""
        vehicle = super().create(vals)
        
        # Auto-generate name if not provided
        if not vehicle.name and vehicle.make_id and vehicle.model_id:
            name_parts = [vehicle.make_id.name, vehicle.model_id.name]
            if vehicle.year:
                name_parts.append(str(vehicle.year))
            if vehicle.color:
                name_parts.append(vehicle.color)
            vehicle.name = ' '.join(name_parts)
        
        return vehicle
    
    def write(self, vals):
        """Override write to handle state changes"""
        result = super().write(vals)
        
        # Update related product template state if vehicle state changes
        if 'state' in vals:
            for vehicle in self:
                if vehicle.product_id2:
                    vehicle.product_id2.write({'state': vals['state']})
        
        return result
    
    @api.onchange('make_id')
    def _onchange_make_id(self):
        """Filter models based on selected make"""
        if self.make_id:
            return {'domain': {'model_id': [('brand_id', '=', self.make_id.id)]}}
        return {'domain': {'model_id': []}}
    
    @api.onchange('model_id', 'year', 'color')
    def _onchange_vehicle_details(self):
        """Auto-generate vehicle name based on details"""
        if self.model_id:
            name_parts = [self.make_id.name, self.model_id.name]
            if self.year:
                name_parts.append(str(self.year))
            if self.color:
                name_parts.append(self.color)
            self.name = ' '.join(name_parts)

   