from odoo import http, fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression


class DealershipWebsite(WebsiteSale):
    @http.route(['/shop/vehicles',
                '/shop/vehicles/page/<int:page>',
                '/shop/vehicles/category/<model("product.public.category"):category>'],
               type='http', auth="public", website=True)
    def shop_vehicles(self, page=0, category=None, search='', ppg=20, **post):
        """Display the vehicle grid with filters."""
        # Initialize domain with vehicle products
        domain = [('is_vehicle', '=', True)]

        # Apply search filters
        if post.get('make'):
            domain = expression.AND([domain, [('make_id', '=', int(post['make']))]])
        if post.get('model'):
            domain = expression.AND([domain, [('model_id', '=', int(post['model']))]])
        if post.get('condition'):
            domain = expression.AND([domain, [('condition', '=', post['condition'])]])
        
        # Price range filter
        if post.get('price_range'):
            price_range = post['price_range'].split('-')
            if len(price_range) == 2:
                min_price, max_price = price_range
                if min_price:
                    domain = expression.AND([domain, [('selling_price', '>=', float(min_price))]])
                if max_price and max_price != '+':
                    domain = expression.AND([domain, [('selling_price', '<=', float(max_price))]])
            elif price_range[0].endswith('+'):
                min_price = float(price_range[0].rstrip('+'))
                domain = expression.AND([domain, [('selling_price', '>=', min_price)]])

        # Get available makes and models for filters
        makes = request.env['fleet.vehicle.model.brand'].search([])
        models = request.env['fleet.vehicle.model'].search([])

        # Search for vehicles
        Product = request.env['product.template']
        vehicles = Product.search(domain)
        total = len(vehicles)

        # Pager
        pager = request.website.pager(
            url='/shop/vehicles',
            total=total,
            page=page,
            step=ppg,
            scope=7,
            url_args=post,
        )

        # Get paginated vehicles
        vehicles = Product.search(domain, limit=ppg, offset=pager['offset'])

        values = {
            'vehicles': vehicles,
            'makes': makes,
            'models': models,
            'search_make': int(post.get('make', 0)),
            'search_model': int(post.get('model', 0)),
            'search_condition': post.get('condition', ''),
            'search_price_range': post.get('price_range', ''),
            'pager': pager,
        }

        return request.render("car_dealership.vehicle_grid", values)

    @http.route(['/shop/vehicle/<model("product.template"):vehicle>'], type='http', auth="public", website=True)
    def vehicle_detail(self, vehicle, **post):
        """Display the vehicle detail page."""
        if not vehicle.exists() or not vehicle.is_vehicle:
            return request.redirect('/shop/vehicles')

        values = {
            'vehicle': vehicle,
            'main_object': vehicle,
        }

        return request.render("car_dealership.vehicle_detail", values)

    @http.route(['/shop/vehicle/inquiry'], type='json', auth="public", website=True)
    def vehicle_inquiry(self, vehicle_id, **post):
        """Handle vehicle inquiry submission."""
        vehicle = request.env['product.template'].browse(int(vehicle_id))
        if not vehicle.exists() or not vehicle.is_vehicle:
            return {'error': 'Vehicle not found'}

        # Create a lead/opportunity
        lead_vals = {
            'name': f"Inquiry for {vehicle.name}",
            'partner_name': post.get('name'),
            'email_from': post.get('email'),
            'phone': post.get('phone'),
            'description': post.get('message'),
            'type': 'opportunity',
            'vehicle_id': vehicle.id,
        }
        lead = request.env['crm.lead'].sudo().create(lead_vals)

        return {
            'success': True,
            'message': 'Your inquiry has been submitted successfully. Our team will contact you shortly.'
        }

    @http.route(['/shop/vehicle/test-drive'], type='json', auth="public", website=True)
    def schedule_test_drive(self, vehicle_id, **post):
        """Handle test drive scheduling."""
        vehicle = request.env['product.template'].browse(int(vehicle_id))
        if not vehicle.exists() or not vehicle.is_vehicle:
            return {'error': 'Vehicle not found'}

        # Create calendar event and lead
        event_start = fields.Datetime.from_string(post.get('datetime'))
        event_stop = event_start + fields.Datetime.from_string('1:00')  # 1-hour test drive

        # Create a lead first
        lead_vals = {
            'name': f"Test Drive Request - {vehicle.name}",
            'partner_name': post.get('name'),
            'email_from': post.get('email'),
            'phone': post.get('phone'),
            'description': f"Test drive scheduled for {event_start}",
            'type': 'opportunity',
            'vehicle_id': vehicle.id,
        }
        lead = request.env['crm.lead'].sudo().create(lead_vals)

        # Create calendar event
        event_vals = {
            'name': f"Test Drive - {vehicle.name}",
            'start': event_start,
            'stop': event_stop,
            'duration': 1.0,
            'partner_ids': [(4, request.env.user.partner_id.id)],
            'user_id': request.env.user.id,
            'vehicle_id': vehicle.id,
        }
        event = request.env['calendar.event'].sudo().create(event_vals)

        return {
            'success': True,
            'message': 'Your test drive has been scheduled. Our team will confirm the appointment shortly.'
        }
