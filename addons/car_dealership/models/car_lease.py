from odoo import models, fields, api
from datetime import date

class CarLease(models.Model):
    _name = 'car.dealership.lease'
    _description = 'Car Lease Contract'
    _order = 'start_date desc'

    name = fields.Char('Lease Reference', required=True, copy=False, default='New')
    car_id = fields.Many2one('car.dealership.car', string='Car', required=True,
                             domain=[('status', 'in', ['available', 'reserved'])])
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)

    # Lease Terms
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    lease_term = fields.Integer('Lease Term (months)', compute='_compute_lease_term', store=True)
    monthly_payment = fields.Monetary('Monthly Payment', currency_field='currency_id')
    deposit = fields.Monetary('Security Deposit', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)

    # Mileage Limits
    annual_mileage_limit = fields.Integer('Annual Mileage Limit (km)', default=20000)
    excess_mileage_rate = fields.Float('Excess Mileage Rate (per km)')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated Early'),
        ('completed', 'Completed'),
    ], string='Status', default='draft')

    # Contract Details
    contract_file = fields.Binary('Contract Document')
    contract_filename = fields.Char('Contract Filename')
    notes = fields.Text('Notes')

    @api.depends('start_date', 'end_date')
    def _compute_lease_term(self):
        for lease in self:
            if lease.start_date and lease.end_date:
                # Calculate months between dates
                months = (lease.end_date.year - lease.start_date.year) * 12
                months += lease.end_date.month - lease.start_date.month
                lease.lease_term = months
            else:
                lease.lease_term = 0

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('car.lease') or 'New'
        lease = super().create(vals)
        # Update car status when lease is created
        if lease.car_id:
            lease.car_id.status = 'leased'
            lease.car_id.lease_id = lease.id
        return lease

    def action_activate(self):
        self.ensure_one()
        product = self.env['product.product'].search([('name', '=', 'Lease Payment')], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'Lease Payment',
                'list_price': self.monthly_payment,
                'type': 'service',
            })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': f'Monthly Lease for {self.car_id.display_name}',
                'price_unit': self.monthly_payment,
                'product_uom_qty': self.lease_term,
            })],
        })
        sale_order.action_confirm()
        self.state = 'active'
        self.car_id.status = 'leased'

    def action_complete(self):
        self.state = 'completed'
        self.car_id.status = 'available'
        self.car_id.lease_id = False