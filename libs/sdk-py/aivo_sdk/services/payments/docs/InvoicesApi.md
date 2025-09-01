# aivo_sdk.InvoicesApi

All URIs are relative to *https://api.aivo.com/payments/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_invoice**](InvoicesApi.md#get_invoice) | **GET** /invoices/{invoiceId} | Get invoice by ID
[**list_invoices**](InvoicesApi.md#list_invoices) | **GET** /invoices | List invoices


# **get_invoice**
> Invoice get_invoice(invoice_id)

Get invoice by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.invoice import Invoice
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.InvoicesApi(api_client)
    invoice_id = 'invoice_id_example' # str | 

    try:
        # Get invoice by ID
        api_response = api_instance.get_invoice(invoice_id)
        print("The response of InvoicesApi->get_invoice:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling InvoicesApi->get_invoice: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **invoice_id** | **str**|  | 

### Return type

[**Invoice**](Invoice.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Invoice retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Invoice not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_invoices**
> ListInvoices200Response list_invoices(tenant_id=tenant_id, subscription_id=subscription_id, status=status, limit=limit, offset=offset)

List invoices

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_invoices200_response import ListInvoices200Response
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/payments/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/payments/v1"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization (JWT): bearerAuth
configuration = aivo_sdk.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.InvoicesApi(api_client)
    tenant_id = 'tenant_id_example' # str |  (optional)
    subscription_id = 'subscription_id_example' # str |  (optional)
    status = 'status_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List invoices
        api_response = api_instance.list_invoices(tenant_id=tenant_id, subscription_id=subscription_id, status=status, limit=limit, offset=offset)
        print("The response of InvoicesApi->list_invoices:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling InvoicesApi->list_invoices: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | [optional] 
 **subscription_id** | **str**|  | [optional] 
 **status** | **str**|  | [optional] 
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListInvoices200Response**](ListInvoices200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Invoices retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

