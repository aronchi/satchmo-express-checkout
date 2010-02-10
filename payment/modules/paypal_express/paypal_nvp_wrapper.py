import urllib, logging
from cgi import parse_qs

from django.conf import settings
from satchmo.utils.dynamic import lookup_url

log = logging.getLogger()

class PayPal:
    """ #PayPal utility class"""
    signature_values = {}
    API_ENDPOINT = ""
    PAYPAL_URL = ""
    return_url = ""
    cancel_url = ""
    shop_logo = ""
    localecode = ""
    
    def __init__(self, payment_module):
        if payment_module.LIVE.value:
            log.debug("live order on %s", payment_module.KEY.value)
            self.PAYPAL_URL = payment_module.POST_URL.value
            self.API_ENDPOINT = payment_module.ENDPOINT_URL.value
            api_signature_username = payment_module.API_SIGNATURE_USERNAME.value
            api_signature_password = payment_module.API_SIGNATURE_PASSWORD.value
            api_signature_code = payment_module.API_SIGNATURE_CODE.value
            
            #account = payment_module.BUSINESS.value
        else:
            log.debug("test order on %s", payment_module.KEY.value)
            self.PAYPAL_URL = payment_module.POST_TEST_URL.value
            self.API_ENDPOINT = payment_module.ENDPOINT_TEST_URL.value
            api_signature_username = payment_module.SANDBOX_API_SIGNATURE_USERNAME.value
            api_signature_password = payment_module.SANDBOX_API_SIGNATURE_PASSWORD.value
            api_signature_code = payment_module.SANDBOX_API_SIGNATURE_CODE.value

        ## Sandbox values
        self.signature_values = {
        'USER' : api_signature_username, 
        'PWD' : api_signature_password, 
        'SIGNATURE' : api_signature_code,
        'VERSION' : '53.0',
        }

        self.signature = urllib.urlencode(self.signature_values) + "&"
        
        
        self.return_url = lookup_url(payment_module, 'satchmo_checkout-step2')
        self.return_url = "http://" + settings.SITE_DOMAIN + self.return_url
        self.cancel_url = lookup_url(payment_module, 'satchmo_checkout-cancel')
        self.cancel_url = "http://" + settings.SITE_DOMAIN + self.cancel_url
        
	if payment_module.SHOP_LOGO.value.startswith("http"):
	    self.shop_logo = payment_module.SHOP_LOGO.value
	else:	
            self.shop_logo = "http://" + settings.SITE_DOMAIN + payment_module.SHOP_LOGO.value
        self.localecode = payment_module.DEFAULT_LOCALECODE.value.upper().encode() # from unicode

    # API METHODS
    def SetExpressCheckout(self, params):
        default_params = {
            'METHOD' : "SetExpressCheckout",
            'NOSHIPPING' : 1,
            'PAYMENTACTION' : 'Authorization',
            'RETURNURL' : self.return_url,
            'CANCELURL' : self.cancel_url,
            'AMT' : 100,
        }
        default_params.update(params)
        params_string = self.signature + urllib.urlencode(default_params)
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_dict = parse_qs(response)
        try:
            response_token = response_dict['TOKEN'][0]
            return response_token
            
        except:
            log.info("Unvalid Paypal API settings")
            assert False
        
    
    def GetExpressCheckoutDetails(self, token, return_all = False):
        default_params = {
            'METHOD' : "GetExpressCheckoutDetails",
            'RETURNURL' : self.return_url, 
            'CANCELURL' : self.cancel_url,  
            'TOKEN' : token,
        }
        #default_params.update(params)
        params_string = self.signature + urllib.urlencode(default_params)
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_dict = parse_qs(response)
        if return_all:
            return response_dict
        try:
            response_token = response_dict['TOKEN'][0]
        except KeyError:
            response_token = response_dict
        return response_token
    
    def DoExpressCheckoutPayment(self, params):
        
        default_params = {
            'METHOD' : "DoExpressCheckoutPayment",
            'PAYMENTACTION' : 'Sale',
            'RETURNURL' : self.return_url,#'http://www.yoursite.com/returnurl', #edit this 
            'CANCELURL' : self.cancel_url,#'http://www.yoursite.com/cancelurl', #edit this 
            #'TOKEN' : token,
            #'AMT' : amt,
            #'PAYERID' : payer_id,
        }
        
        default_params.update(params)
                     
        params_string = self.signature + urllib.urlencode(default_params)
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_tokens = {}
        for token in response.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens
        
    def GetTransactionDetails(self, tx_id):
        params = {
            'METHOD' : "GetTransactionDetails", 
            'TRANSACTIONID' : tx_id,
        }
        params_string = self.signature + urllib.urlencode(params)
        response = urllib.urlopen(self.API_ENDPOINT, params_string).read()
        response_tokens = {}
        for token in response.split('&'):
            response_tokens[token.split("=")[0]] = token.split("=")[1]
        for key in response_tokens.keys():
                response_tokens[key] = urllib.unquote(response_tokens[key])
        return response_tokens
