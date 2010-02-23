import logging
#import urllib2

from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils.http import urlencode
from django.utils.translation import ugettext as _
#from sys import exc_info
#from traceback import format_exception

from satchmo.configuration import config_get_group
from satchmo.configuration import config_value 
from satchmo.shop.models import Order, OrderPayment, Cart
from satchmo.payment.utils import record_payment, create_pending_payment
from satchmo.payment.views import payship
#from satchmo.payment.config import payment_live
from satchmo.tax.models import TaxRate
from satchmo.utils.dynamic import lookup_url, lookup_template
from paypal_nvp_wrapper import PayPal
from decimal import Decimal
from satchmo.contact.models import Contact, AddressBook, PhoneNumber
from satchmo.l10n.models import Country
#from django.utils.http import urlquote
import unicodedata
from satchmo.contact import CUSTOMER_ID



log = logging.getLogger()

def pp_express_pay_ship_info_verify(request, payment_module):
    """Verify customer and cart.
    Returns:
    True, contact, cart on success
    False, destination of failure
    """
    # Get Customer Info from Paypal Express Checkout
    
    paypal = PayPal(payment_module)

    if 'paypal_express_token' in request.session:
        paypal_express_token = request.session['paypal_express_token']
    else:
        # If the user didn't get the authorization I redirect to the request authorization page
        return False
        
    
    response_dict = paypal.GetExpressCheckoutDetails(paypal_express_token, return_all=True)
    
    if 'SHIPTOSTREET' not in response_dict:
        # If the user didn't get the authorization I redirect to the request authorization page
        return False
        
    email = response_dict["EMAIL"][0]
    first_name = response_dict["FIRSTNAME"][0]
    last_name = response_dict["LASTNAME"][0]
    addressee = response_dict["SHIPTONAME"][0]
    street1 = response_dict["SHIPTOSTREET"][0]
    
    try:
        street2 = response_dict["SHIPTOSTREET2"][0]
    except:
        street2 = ""
        
    city = response_dict["SHIPTOCITY"][0]
    
    try:
        state = response_dict["SHIPTOSTATE"][0]
    except:
        state = " "
    postal_code = response_dict["SHIPTOZIP"][0]
    country_code = response_dict["SHIPTOCOUNTRYCODE"][0]

    country = Country.objects.get(iso2_code__iexact=country_code)
    # I get users notes

    if request.user.is_authenticated():
        try:
            contact = Contact.objects.get(user=request.user) # If the user is authenticated I don't neet to create a new contact
            contact.email = email
            contact.first_name = first_name
            contact.last_name = last_name
            
            # I delete the user shipping address to overwrite with paypal express data
            try:
                contact.shipping_address.delete()
            except:
                pass
        
            # I delete the user phone number to overwrite with paypal express data
            try:
                contact.primary_phone.delete()
            except:
                pass

        except:
            pass
        
    elif request.session.get(CUSTOMER_ID):
            try:
                contact = Contact.objects.get(id=request.session[CUSTOMER_ID])
                contact.email = email
                contact.first_name = first_name
                contact.last_name = last_name
                
                # I delete the user shipping address to overwrite with paypal express data
                try:
                    contact.shipping_address.delete()
                except:
                    pass
        
                # I delete the user phone number to overwrite with paypal express data
                try:
                    contact.primary_phone.delete()
                except:
                    pass
                
            except Contact.DoesNotExist:
                del request.session[CUSTOMER_ID]
        
            
            
    try:
        contact    
    except NameError:
        try: # If a user with the same name, email and last name exists, I get that instead of a new contact creation
            contact = Contact.objects.filter(email__iexact=email).filter(first_name__iexact=first_name).filter(last_name__iexact=last_name)[0]
        
        except:    
            # if it doesn't exists, I create it
            contact = Contact(email=email, first_name = first_name, last_name=last_name)

    # If the user wrote a note, I save it
    try:
        #if the user exists, I overwrite his contact data
        contact.notes = contact.notes + '\n' + response_dict["NOTE"][0]
             
    except:
            pass
    
        


    # I save my contact
    contact.save()
    #request.session['CUSTOMER_ID'] = contact.id
    request.session[CUSTOMER_ID] = contact.id
    
 
    shipping_address = AddressBook(addressee=addressee, contact=contact, street1=street1, street2=street2,city = city, state=state, postal_code=postal_code,\
                                   country=country, is_default_shipping=True)
    shipping_address.save()
    
    #billing_address = AddressBook(addressee=addressee, contact=contact, street1=street1, street2=street2,city = city, state=state, postal_code=postal_code,\
    #                               country=country, is_default_shipping=True)
    #billing_address.save()
    
    try:
        phone = PhoneNumber(contact=contact, phone=response_dict["PHONENUM"][0], primary=True, type="Home")
        phone.save()
    except:
        log.debug("PayPal Error importing phone number: " + repr(response_dict))

    # Verify that we still have items in the cart.
    tempCart = Cart.objects.from_request(request)
    tempCart.customer = contact
    tempCart.save()
    
    if tempCart.numItems == 0:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return (False, render_to_response(template, RequestContext(request)))


    return (True, contact, tempCart)

def pp_express_base_pay_ship_info(request, payment_module, form_handler, template):
    results = pp_express_pay_ship_info_verify(request, payment_module)
    
    # If needed value are not correct, I redirect to the first page on paypal
    if results is False:
        url = urlresolvers.reverse("PAYPAL_EXPRESS_satchmo_checkout")
        return HttpResponseRedirect(url)
         
    if not results[0]:
        return results[1]

    contact = results[1]
    working_cart = results[2]

    results = form_handler(request, contact, working_cart, payment_module)
    if results[0]:
        return results[1]

    form = results[1]
    return payship.pay_ship_render_form(request, form, template, payment_module, working_cart)


def pay_ship_info(request):
    return pp_express_base_pay_ship_info(request,
        config_get_group('PAYMENT_PAYPAL_EXPRESS'), payship.simple_pay_ship_process_form,
        'checkout/paypal_express/pay_ship.html')
    
def paypal_express_cancel(request):
    """Returns to the cart after the user cancels his payment on PayPal Express Checkout"""
    url = urlresolvers.reverse("satchmo_cart")
    return HttpResponseRedirect(url)     

def unicode_to_ascii(string):
    return unicodedata.normalize('NFKD', string).encode('ascii','ignore')

    
def paypal_express_request_authorization(request):
    """Requests payment authorization for the payment with SetExpressCheckout"""
    
    payment_module = config_get_group('PAYMENT_PAYPAL_EXPRESS')
    
    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))
    
    
    #total = tempCart.total
    try:
        maxTaxRate = TaxRate.objects.all().order_by('-percentage')[0].percentage
    except:
        maxTaxRate = 0
    maxTaxesAmount = tempCart.total * maxTaxRate
    
    maxShippingCosts = Decimal(payment_module.MAX_SHIPPING_COSTS.value)
    
    max_amt =  '%.2f' % (tempCart.total + maxTaxesAmount + maxShippingCosts)
    amt = '%.2f' % (tempCart.total)

    paypal = PayPal(payment_module)
    
    noshipping = 0        

    params = {
            'METHOD' : "SetExpressCheckout",
            'NOSHIPPING' : noshipping, #1,
            'PAYMENTACTION' : 'Authorization',
            'CURRENCYCODE' : payment_module.CURRENCY_CODE.value.encode(),  # from Unicode
            'ALLOWNOTE' : 1, #true
            'AMT' : amt,
            'MAXAMT': max_amt,
            'LANDINGPAGE' : "Billing",
            'REQCONFIRMSHIPPING': 0,
            'SOLUTIONTYPE': "Sole", # Do not require forced paypal registration
            'HDRIMG': paypal.shop_logo
    #        'HANDLINGAMT' : order.shipping_cost, 
    #        'ITEMAMT' : order.total,
    #        'TAXAMT': order.tax,
    }
    
    if request.LANGUAGE_CODE:
        params["LOCALECODE"]=request.LANGUAGE_CODE.upper().encode()
    elif request.META["HTTP_ACCEPT_LANGUAGE"]:
        params["LOCALECODE"]=request.META["HTTP_ACCEPT_LANGUAGE"][:2].upper() # I set the paypal language
    else:
        params["LOCALECODE"]= paypal.localecode
   
     
    # If the user is authenticated I prepopulate paypal express checkout with its data
    if request.user.is_authenticated():
        try:
            contact = Contact.objects.get(user=request.user)
            shipping_address = contact.shipping_address
            phone = contact.primary_phone
            
            params["EMAIL"] = unicodedata.normalize('NFC', contact.email).encode('ascii','ignore')
            params["ADDRESSOVERRIDE"] = 1
            if shipping_address.addressee:
                params["NAME"] = unicode_to_ascii(shipping_address.addressee)
            else:
                params["NAME"] = unicode_to_ascii(contact.first_name+ " " + contact.second_name)
                
            params["LOCALECODE"] = shipping_address.country.iso2_code
            params["SHIPTOSTREET"] = unicode_to_ascii(shipping_address.street1)
            params["SHIPTOSTREET2"] = unicode_to_ascii(shipping_address.street2)
            params["SHIPTOCITY"] = unicode_to_ascii(shipping_address.city)
            params["SHIPTOSTATE"] = unicode_to_ascii(shipping_address.state)
            params["SHIPTOZIP"] = unicode_to_ascii(shipping_address.postal_code)
            params["SHIPTOCOUNTRY"] = shipping_address.country.iso2_code
            params["PHONENUM"] = unicode_to_ascii(phone.phone)
            
        except:
            pass #user is authenticated but he haven't contact
        
    pp_token = paypal.SetExpressCheckout(params)
    express_token = paypal.GetExpressCheckoutDetails(pp_token)
    url= paypal.PAYPAL_URL + express_token
    
    request.session['paypal_express_token'] = pp_token
    
    # I save my cart to get it once finished
    #request.session['cart_id'] = tempCart
        
   


    return HttpResponseRedirect(url)        
        
def paypal_express_pay(request):
    """Process the real payment on PayPal Express Checkout with DoExpressCheckoutPayment"""

    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    # Check if the order is still valid
    if not order.validate(request):
        context = RequestContext(request,
            {'message': _('Your order is no longer valid.')})
        return render_to_response('shop_404.html', context)
    

    payment_module = config_get_group('PAYMENT_PAYPAL_EXPRESS')
    #amount = '%.2f' % (order.total)
    paypal = PayPal(payment_module)
    
    shipping_amount = order.shipping_cost
    shipping_discount = order.shipping_discount
    

    
    if 'paypal_express_token' in request.session:
        paypal_express_token = request.session['paypal_express_token']
        response_getDetails = paypal.GetExpressCheckoutDetails(paypal_express_token, return_all=True)
        params = {
            'PAYERID' : response_getDetails["PAYERID"][0],
            'CURRENCYCODE' : response_getDetails["CURRENCYCODE"][0],
            'AMT' : '%.2f' % order.total,
            'ITEMAMT' : '%.2f' % order.sub_total,
            'SHIPPINGAMT' : '%.2f' % order.shipping_cost,
            'SHIPPINGDISCOUNT' : '%.2f' % order.shipping_discount,
            'TAXAMT' : '%.2f' % (order.tax - order.discount),
            'TOKEN' : paypal_express_token,
        }
        
        # This function does the payment
        data = paypal.DoExpressCheckoutPayment(params )
      

    #try:
    
    log.debug("PayPal Express Checkout data: " + repr(data))
    
    if not 'PAYMENTSTATUS' in data or not data['PAYMENTSTATUS'] == 'Completed':
    #if not 'payment_status' in data or not data['payment_status'] == "Completed":
        # We want to respond to anything that isn't a payment - but we won't insert into our database.
        log.info("Ignoring IPN data for non-completed payment.")
         
        # I show a failed payment error
        template = lookup_template(payment_module, 'checkout/paypal_express/failed.html')

        # {'ACK': 'Failure', 'TIMESTAMP': '2009-02-28T13:48:55Z', 'L_SEVERITYCODE0': 'Error', 'L_SHORTMESSAGE0': 'Transaction cannot complete.', 'L_LONGMESSAGE0': 'The transaction cannot complete successfully.  Instruct the customer to use an alternative payment method.', 'VERSION': '53.0', 'BUILD': '845846', 'L_ERRORCODE0': '10417', 'CORRELATIONID': 'be804544f01'}

        ctx = RequestContext(request, {'order': order,
             'data': repr(data),
             'ack': data["ACK"],
             #'severity_code': data["L_SEVERITYCODE0"],
             #'short_message': data["L_SHORTMESSAGE0"],
             #'long_message': data["L_LONGMESSAGE0"],
             #'error_code': data["L_ERRORCODE0"],
        })

        # Li aggiungo fuori perché se ne manca uno altrimenti restituisce un keyerror
        try:
            ctx["severity_code"]= data["L_SEVERITYCODE0"]
        except:
            pass

        try:
            ctx["short_message"]= data["L_SHORTMESSAGE0"]
        except:
            pass

         
        try:
            ctx["long_message"]= data["L_LONGMESSAGE0"]
        except:
            pass

        try:
            ctx["error_code"]=data["L_ERRORCODE0"]
        except:
            pass
        
        return render_to_response(template, ctx)
        

    txn_id = data['TRANSACTIONID']
    
    if not OrderPayment.objects.filter(transaction_id=txn_id).count():
        
    # If the payment hasn't already been processed:
        #order = Order.objects.get(pk=invoice)         
        order.add_status(status='Pending', notes=_("Paid through PayPal Express Checkout."))
        #orderstatus = order.status
        
        record_payment(order, payment_module, amount=order.total, transaction_id=txn_id)
        notes_changed = False
        if order.notes:
                notes = order.notes + "\n"
        else:
                notes = ""
                
        # Retrieving notes from paypal NOTE field
        if 'NOTE' in response_getDetails:
            notes_changed = True
	    
	    response_notes = response_getDetails['NOTE'][0] # If I get some problems, the error will include notes if I put it in a variable.
            notes = u"\n%s \n%s \n%s" % (notes, _('---Comment via Paypal EXPRESS CHECKOUT---') ,response_notes )
            log.debug("Saved order notes from Paypal Express Checkout")
        
        # Retrieving notes from confirmation page
        if (request.method == "POST") and ('note' in request.POST) and (request.POST['note'] != ""):
            notes_changed = True
            #notes = notes + u'\n\n'  + _('---Notes sent by confirm Order Form---') + u'\n' + request.POST['note']
            notes = u"%s \n\n%s \n %s" % (notes,  _('---Notes sent by confirm Order Form---'), request.POST['note'])
            log.debug("Saved order notes from Confirm Order Page")    
        
        # If I must add some notes to my order
        if notes_changed:
            order.notes = notes
            order.save()
        
        for item in order.orderitem_set.filter(product__subscriptionproduct__recurring=True, completed=False):
            item.completed = True
            item.save()


        for cart in Cart.objects.filter(customer=order.contact):
            cart.empty()

        # I remove the token from the session
        request.session['paypal_express_token']   
                
            #order.save()
                    
    #except:
    #        log.exception(''.join(format_exception(*exc_info())))
    #        assert False

    url = urlresolvers.reverse("PAYPAL_EXPRESS_satchmo_checkout-success")
    return HttpResponseRedirect(url)     
 

def confirm_info(request):
    """Shows the user its order details and ask confirmation to send to the real payment function"""
    
    payment_module = config_get_group('PAYMENT_PAYPAL_EXPRESS')

    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0:
        template = lookup_template(payment_module, 'checkout/empty_cart.html')
        return render_to_response(template, RequestContext(request))

    # Check if the order is still valid
    if not order.validate(request):
        context = RequestContext(request,
            {'message': _('Your order is no longer valid.')})
        return render_to_response('shop_404.html', context)

    template = lookup_template(payment_module, 'checkout/paypal_express/confirm.html')

        
    create_pending_payment(order, payment_module)
    default_view_tax = config_value('TAX', 'DEFAULT_VIEW_TAX') 
  
    recurring = None
    order_items = order.orderitem_set.all()
  
    ctx = RequestContext(request, {'order': order,
     'post_url': urlresolvers.reverse("PAYPAL_EXPRESS_satchmo_checkout-step4"),
     'default_view_tax': default_view_tax, 
     'currency_code': payment_module.CURRENCY_CODE.value,
     'invoice': order.id,

    })

    return render_to_response(template, ctx)
