# aivo_sdk.SubscriptionApi

All URIs are relative to *https://api.aivo.com/admin/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_tenant_subscription**](SubscriptionApi.md#get_tenant_subscription) | **GET** /subscription | Get tenant subscription details


# **get_tenant_subscription**
> SubscriptionDetails get_tenant_subscription(tenant_id)

Get tenant subscription details

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.subscription_details import SubscriptionDetails
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/admin/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/admin/v1"
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
    api_instance = aivo_sdk.SubscriptionApi(api_client)
    tenant_id = '456e7890-e89b-12d3-a456-426614174000' # str | Tenant ID to get subscription for

    try:
        # Get tenant subscription details
        api_response = api_instance.get_tenant_subscription(tenant_id)
        print("The response of SubscriptionApi->get_tenant_subscription:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling SubscriptionApi->get_tenant_subscription: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**| Tenant ID to get subscription for | 

### Return type

[**SubscriptionDetails**](SubscriptionDetails.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Subscription details retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

