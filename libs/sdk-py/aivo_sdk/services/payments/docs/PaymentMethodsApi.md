# aivo_sdk.PaymentMethodsApi

All URIs are relative to *https://api.aivo.com/payments/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_payment_method**](PaymentMethodsApi.md#add_payment_method) | **POST** /payment-methods | Add payment method
[**list_payment_methods**](PaymentMethodsApi.md#list_payment_methods) | **GET** /payment-methods | List payment methods
[**remove_payment_method**](PaymentMethodsApi.md#remove_payment_method) | **DELETE** /payment-methods/{paymentMethodId} | Remove payment method


# **add_payment_method**
> PaymentMethod add_payment_method(add_payment_method_request)

Add payment method

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.add_payment_method_request import AddPaymentMethodRequest
from aivo_sdk.models.payment_method import PaymentMethod
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
    api_instance = aivo_sdk.PaymentMethodsApi(api_client)
    add_payment_method_request = aivo_sdk.AddPaymentMethodRequest() # AddPaymentMethodRequest | 

    try:
        # Add payment method
        api_response = api_instance.add_payment_method(add_payment_method_request)
        print("The response of PaymentMethodsApi->add_payment_method:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PaymentMethodsApi->add_payment_method: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **add_payment_method_request** | [**AddPaymentMethodRequest**](AddPaymentMethodRequest.md)|  | 

### Return type

[**PaymentMethod**](PaymentMethod.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Payment method added successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_payment_methods**
> List[PaymentMethod] list_payment_methods(tenant_id)

List payment methods

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.payment_method import PaymentMethod
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
    api_instance = aivo_sdk.PaymentMethodsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 

    try:
        # List payment methods
        api_response = api_instance.list_payment_methods(tenant_id)
        print("The response of PaymentMethodsApi->list_payment_methods:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling PaymentMethodsApi->list_payment_methods: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | 

### Return type

[**List[PaymentMethod]**](PaymentMethod.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Payment methods retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **remove_payment_method**
> remove_payment_method(payment_method_id)

Remove payment method

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
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
    api_instance = aivo_sdk.PaymentMethodsApi(api_client)
    payment_method_id = 'payment_method_id_example' # str | 

    try:
        # Remove payment method
        api_instance.remove_payment_method(payment_method_id)
    except Exception as e:
        print("Exception when calling PaymentMethodsApi->remove_payment_method: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **payment_method_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Payment method removed successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Payment method not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

