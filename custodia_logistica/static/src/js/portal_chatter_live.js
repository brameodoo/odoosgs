/** @odoo-module **/

import { publicWidget } from "@web/legacy/js/public/public_widget";

// Verificamos que publicWidget y registry existan antes de extender
if (publicWidget && publicWidget.registry) {
    publicWidget.registry.CustodiaChatterLive = publicWidget.Widget.extend({
        selector: '#service_chatter',

        start: function () {
            this.resId = parseInt(this.$el.attr('data-res-id'));
            if (this.resId && this.call) {
                this.call('bus_service', 'addChannel', `custodia_service_${this.resId}`);
                this.call('bus_service', 'subscribe', `custodia_service_${this.resId}`, this._onNotification.bind(this));
            }
            return this._super.apply(this, arguments);
        },

        _onNotification: function (payload) {
            if (payload && payload.type === 'mail.record/insert' && payload.res_id === this.resId) {
                const $composer = this.$('.o_portal_chatter_composer_body');
                if ($composer.length === 0 || !$composer.is(':focus')) {
                    this._refreshChatter();
                }
            }
        },

        _refreshChatter: function() {
            const $messages = this.$('.o_portal_chatter_messages');
            if ($messages.length) {
                $messages.load(window.location.href + " .o_portal_chatter_messages > *");
            }
        }
    });
}
