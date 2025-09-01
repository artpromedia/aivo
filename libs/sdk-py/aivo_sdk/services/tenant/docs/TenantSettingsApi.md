# aivo_sdk.TenantSettingsApi

All URIs are relative to *https://api.aivo.com/tenant/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_tenant_settings**](TenantSettingsApi.md#get_tenant_settings) | **GET** /tenants/{tenantId}/settings | Get tenant settings
[**update_tenant_settings**](TenantSettingsApi.md#update_tenant_settings) | **PUT** /tenants/{tenantId}/settings | Update tenant settings


# **get_tenant_settings**
> TenantSettings get_tenant_settings(tenant_id)

Get tenant settings

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.tenant_settings import TenantSettings
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/tenant/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/tenant/v1"
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
    api_instance = aivo_sdk.TenantSettingsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 

    try:
        # Get tenant settings
        api_response = api_instance.get_tenant_settings(tenant_id)
        print("The response of TenantSettingsApi->get_tenant_settings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantSettingsApi->get_tenant_settings: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | 

### Return type

[**TenantSettings**](TenantSettings.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Tenant settings retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_tenant_settings**
> TenantSettings update_tenant_settings(tenant_id, tenant_settings)

Update tenant settings

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.tenant_settings import TenantSettings
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/tenant/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/tenant/v1"
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
    api_instance = aivo_sdk.TenantSettingsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 
    tenant_settings = aivo_sdk.TenantSettings() # TenantSettings | 

    try:
        # Update tenant settings
        api_response = api_instance.update_tenant_settings(tenant_id, tenant_settings)
        print("The response of TenantSettingsApi->update_tenant_settings:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantSettingsApi->update_tenant_settings: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  | 
 **tenant_settings** | [**TenantSettings**](TenantSettings.md)|  | 

### Return type

[**TenantSettings**](TenantSettings.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Tenant settings updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

