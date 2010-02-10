from django.conf.urls.defaults import *
from satchmo.configuration import config_get_group
from django.conf import settings

config = config_get_group('PAYMENT_PAYPAL_EXPRESS')

urlpatterns = patterns('',
     (r'^$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.paypal_express_request_authorization', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout'),
     (r'^shipment/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.pay_ship_info', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-step2'),
     (r'^confirm/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.confirm_info', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-step3'),
     #(r'^confirm/$', 'payment.modules.paypal.views.confirm_info', {'SSL': config.SSL.value}, 'PAYPAL_satchmo_checkout-step3'),
     (r'^pay/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.paypal_express_pay', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-step4'),
     #(r'^confirm/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.confirm_info', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-step3'),
     (r'^success/$', 'satchmo.payment.views.checkout.success', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-success'),
     #(r'^cart/$', 'cart.display', {}, 'satchmo_cart'),
     #(r'^paypal_express_success/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.paypal_express_pay', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-step2'),
     (r'^cancel/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.paypal_express_cancel', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-cancel'),
     #(r'^failed/$', settings.PROJECTNAME +'.payment.modules.paypal_express.views.paypal_express_failed', {'SSL': config.SSL.value}, 'PAYPAL_EXPRESS_satchmo_checkout-failed'),
)