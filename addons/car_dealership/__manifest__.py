{
    'name': 'car_dealership',
    'version': '1.0',
    'description': """The Car Dealership module provides an all-in-one solution for managing car dealership operations within Odoo. Key features include:
        - **Car Inventory Management**: Track new and used cars with detailed specifications (make, model, VIN, mileage, etc.).
        - **Sales and Leasing**: Handle sales orders and lease contracts with automated invoicing for monthly payments and down payments.
        - **Test Drives**: Schedule and manage customer test drive bookings.
        - **Service Appointments**: Organize maintenance, repairs, and inspections with scheduling capabilities.
        - **Customer Portal**: Allow customers to view their lease details and book test drives.
        - **Reporting**: Generate lease contract reports and analyze dealership performance with dashboards.
        This module integrates seamlessly with Odoo's Sales, Accounting, and Portal modules for a streamlined dealership experience.
    """,
    'author': 'Ojo Ayanfe - Mattobel',
    'category': 'Sales',
    'depends': ['base', 'product', 'sale_management', 'account', 'contacts',
                'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/car_views.xml',
        'views/car_lease_views.xml',
        'views/car_model_views.xml',
        'views/car_make_views.xml',
        'views/car_feature_views.xml',
        'views/car_service_views.xml',
        'views/test_drive_views.xml',
        'views/website_templates.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'car_dealership/static/src/scss/website_styles.scss',
            'car_dealership/static/src/js/website_scripts.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
