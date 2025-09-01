# aivo_sdk.NamespacesApi

All URIs are relative to *https://api.aivo.com/admin/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_tenant_namespaces**](NamespacesApi.md#get_tenant_namespaces) | **GET** /namespaces | Get tenant namespaces overview


# **get_tenant_namespaces**
> NamespacesOverview get_tenant_namespaces(tenant_id)

Get tenant namespaces overview

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.namespaces_overview import NamespacesOverview
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
    api_instance = aivo_sdk.NamespacesApi(api_client)
    tenant_id = '456e7890-e89b-12d3-a456-426614174000' # str | Tenant ID to get namespaces for

    try:
        # Get tenant namespaces overview
        api_response = api_instance.get_tenant_namespaces(tenant_id)
        print("The response of NamespacesApi->get_tenant_namespaces:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling NamespacesApi->get_tenant_namespaces: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**| Tenant ID to get namespaces for | 

### Return type

[**NamespacesOverview**](NamespacesOverview.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Namespaces overview retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

