# aivo_sdk.CouponsApi

All URIs are relative to *<https://api.aivo.com/payments/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_coupon**](CouponsApi.md#create_coupon) | **POST** /coupons | Create coupon
[**list_coupons**](CouponsApi.md#list_coupons) | **GET** /coupons | List coupons

# **create_coupon**
>
> Coupon create_coupon(create_coupon_request)

Create coupon

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.coupon import Coupon
from aivo_sdk.models.create_coupon_request import CreateCouponRequest
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
    api_instance = aivo_sdk.CouponsApi(api_client)
    create_coupon_request = aivo_sdk.CreateCouponRequest() # CreateCouponRequest | 

    try:
        # Create coupon
        api_response = api_instance.create_coupon(create_coupon_request)
        print("The response of CouponsApi->create_coupon:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CouponsApi->create_coupon: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_coupon_request** | [**CreateCouponRequest**](CreateCouponRequest.md)|  |

### Return type

[**Coupon**](Coupon.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Coupon created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_coupons**
>
> List[Coupon] list_coupons(tenant_id=tenant_id, active=active, limit=limit)

List coupons

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.coupon import Coupon
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
    api_instance = aivo_sdk.CouponsApi(api_client)
    tenant_id = 'tenant_id_example' # str |  (optional)
    active = True # bool |  (optional)
    limit = 20 # int |  (optional) (default to 20)

    try:
        # List coupons
        api_response = api_instance.list_coupons(tenant_id=tenant_id, active=active, limit=limit)
        print("The response of CouponsApi->list_coupons:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling CouponsApi->list_coupons: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | [optional]
 **active** | **bool**|  | [optional]
 **limit** | **int**|  | [optional] [default to 20]

### Return type

[**List[Coupon]**](Coupon.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Coupons retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
