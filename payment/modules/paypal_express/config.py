from satchmo.configuration import *
from django.utils.translation import ugettext_lazy as _


PAYMENT_MODULES = config_get('PAYMENT', 'MODULES')
PAYMENT_MODULES.add_choice(('PAYMENT_PAYPAL_EXPRESS', _('Paypal Express Checkout Payment Settings')))

PAYMENT_GROUP = ConfigurationGroup('PAYMENT_PAYPAL_EXPRESS', 
    _('Paypal Express Checkout Payment Module Settings'), 
    requires=PAYMENT_MODULES,
    ordering = 101)

config_register_list(

StringValue(PAYMENT_GROUP,
    'CURRENCY_CODE',
    description=_('Currency Code'),
    help_text=_('Currency code for Paypal transactions.'),
    default = 'USD'),
    
StringValue(PAYMENT_GROUP,
    'POST_URL',
    description=_('Post URL'),
    help_text=_('The Paypal URL for real transaction posting.'),
    default="https://www.paypal.com/cgi-bin/webscr&cmd=_express-checkout&token="),

StringValue(PAYMENT_GROUP,
    'POST_TEST_URL',
    description=_('Post URL Test'),
    help_text=_('The Paypal URL for test transaction posting.'),
    default="https://www.sandbox.paypal.com/cgi-bin/webscr&cmd=_express-checkout&token="),
    
StringValue(PAYMENT_GROUP,
    'ENDPOINT_URL',
    description=_('Server Endpoint'),
    help_text=_('PayPal live production server for use with API signatures'),
    default="https://api-3t.paypal.com/nvp"),

StringValue(PAYMENT_GROUP,
    'ENDPOINT_TEST_URL',
    description=_('Test Server Endpoint'),
    help_text=_('PayPal sandbox server for use with API signatures'),
    default="https://api-3t.sandbox.paypal.com/nvp"),    

StringValue(PAYMENT_GROUP,
    'SANDBOX_API_SIGNATURE_PASSWORD',
    description=_('SANDBOX Paypal API Password'),
    help_text=_('The PASSWORD of your API signature on Paypal'),
    default=""),

StringValue(PAYMENT_GROUP,
    'SANDBOX_API_SIGNATURE_USERNAME',
    description=_('SANDBOX Paypal API Username'),
    help_text=_('The username of your API signature on Paypal'),
    default=""),    

StringValue(PAYMENT_GROUP,
    'SANDBOX_API_SIGNATURE_CODE',
    description=_('SANDBOX Paypal API Signature Code'),
    help_text=_('The code of your API signature on PayPal'),
    default=""),    
    
StringValue(PAYMENT_GROUP,
    'API_SIGNATURE_PASSWORD',
    description=_('Paypal API Password'),
    help_text=_('The PASSWORD of your API signature on Paypal'),
    default=""),

StringValue(PAYMENT_GROUP,
    'API_SIGNATURE_USERNAME',
    description=_('Paypal API Username'),
    help_text=_('The username of your API signature on Paypal'),
    default=""),    

StringValue(PAYMENT_GROUP,
    'API_SIGNATURE_CODE',
    description=_('Paypal API Signature Code'),
    help_text=_('The code of your API signature on PayPal'),
    default=""),    

StringValue(PAYMENT_GROUP,
    'RETURN_ADDRESS',
    description=_('Return URL'),
    help_text=_('Where Paypal will return the customer after the purchase is complete.  This can be a named url and defaults to the standard checkout success.'),
    default="PAYPAL_satchmo_checkout-success"),
    
StringValue(PAYMENT_GROUP,
    'CANCEL_ADDRESS',
    description=_('Return Cancel URL'),
    help_text=_('Where Paypal will return the customer if the purchase raises an error.'),
    default=""),    

StringValue(PAYMENT_GROUP,
    'MAX_SHIPPING_COSTS',
    description=_('Max Shipping Costs to add to the Order'),
    help_text=_('This value must be the max amount that users can pay for shipping, it\'s used only to request authorizations and not really charged to the user (he will be charged for the exact amount)'),
    default="200"),    
        
BooleanValue(PAYMENT_GROUP, 
    'SSL', 
    description=_("Use SSL for the module checkout pages?"), 
    default=False),
    
BooleanValue(PAYMENT_GROUP, 
    'LIVE', 
    description=_("Accept real payments"),
    help_text=_("False if you want to be in test mode"),
    default=False),
    
StringValue(PAYMENT_GROUP,
    'SHOP_LOGO',
    description=_('Shop Logo'),
    help_text=_("URI to the logo for the store"),
    default="/static/images/logo.png"),
    
StringValue(PAYMENT_GROUP,
    'DEFAULT_LOCALECODE',
    description=_('Default LOCALECODE'),
    help_text=_("The locale code used for paypal pages"),
    default="EN"),        
    
ModuleValue(PAYMENT_GROUP,
    'MODULE',
    description=_('Implementation module'),
    hidden=True,
    default = settings.PROJECTNAME + '.payment.modules.paypal_express'),
    
StringValue(PAYMENT_GROUP,
    'KEY',
    description=_("Module key"),
    hidden=True,
    default = 'PAYPAL_EXPRESS'),

StringValue(PAYMENT_GROUP,
    'LABEL',
    description=_('English name for this group on the checkout screens'),
    default = 'PayPal Express Checkout',
    help_text = _('This will be passed to the translation utility')),

StringValue(PAYMENT_GROUP,
    'URL_BASE',
    description=_('The url base used for constructing urlpatterns which will use this module'),
    default = '^paypal_express/')
)
