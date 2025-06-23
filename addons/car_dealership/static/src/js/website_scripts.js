odoo.define('car_dealership.website', function (require) {
    'use strict';
    const publicWidget = require('web.public.widget');
    const { Component } = owl;

    publicWidget.registry.CarDealership = publicWidget.Widget.extend({
        selector: '.car-card',
        events: {
            'click .test-drive-btn': '_onClickTestDrive',
        },
        _onClickTestDrive: function (ev) {
            const carId = ev.currentTarget.dataset.carId;
            document.getElementById('car_id').value = carId;
            const modal = new bootstrap.Modal(document.getElementById('test-drive-modal'));
            modal.show();
        },
    });

    return publicWidget.registry.CarDealership;
});