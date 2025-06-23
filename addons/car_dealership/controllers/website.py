from odoo import http
from odoo.http import request

class CarDealershipWebsite(http.Controller):
    @http.route('/cars', type='http', auth='public', website=True)
    def list_cars(self, **kwargs):
        cars = request.env['car.dealership.car'].search([
            ('status', '=', 'available')
        ])
        return request.render('car_dealership.car_list_template', {
            'cars': cars,
        })

    @http.route('/cars/test_drive', type='http', auth='public', website=True, methods=['POST'])
    def submit_test_drive(self, **post):
        car_id = post.get('car_id')
        name = post.get('name')
        email = post.get('email')
        date = post.get('date')
        if car_id and name and email and date:
            request.env['car.dealership.test_drive'].sudo().create({
                'car_id': int(car_id),
                'name': name,
                'email': email,
                'date': date,
            })
            return request.render('car_dealership.test_drive_success', {
                'message': 'Test drive request submitted successfully!'
            })
        return request.redirect('/cars')