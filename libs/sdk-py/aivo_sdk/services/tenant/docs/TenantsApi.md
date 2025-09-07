# aivo_sdk.TenantsApi

All URIs are relative to *<https://api.aivo.com/tenant/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_tenant**](TenantsApi.md#create_tenant) | **POST** /tenants | Create new tenant
[**delete_tenant**](TenantsApi.md#delete_tenant) | **DELETE** /tenants/{tenantId} | Delete tenant
[**get_tenant**](TenantsApi.md#get_tenant) | **GET** /tenants/{tenantId} | Get tenant by ID
[**list_tenants**](TenantsApi.md#list_tenants) | **GET** /tenants | List tenants
[**update_tenant**](TenantsApi.md#update_tenant) | **PUT** /tenants/{tenantId} | Update tenant

# **create_tenant**
>
> Tenant create_tenant(create_tenant_request)

Create new tenant

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_tenant_request import CreateTenantRequest
from aivo_sdk.models.tenant import Tenant
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
    api_instance = aivo_sdk.TenantsApi(api_client)
    create_tenant_request = aivo_sdk.CreateTenantRequest() # CreateTenantRequest | 

    try:
        # Create new tenant
        api_response = api_instance.create_tenant(create_tenant_request)
        print("The response of TenantsApi->create_tenant:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantsApi->create_tenant: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_tenant_request** | [**CreateTenantRequest**](CreateTenantRequest.md)|  |

### Return type

[**Tenant**](Tenant.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Tenant created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_tenant**
>
> delete_tenant(tenant_id)

Delete tenant

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
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
    api_instance = aivo_sdk.TenantsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 

    try:
        # Delete tenant
        api_instance.delete_tenant(tenant_id)
    except Exception as e:
        print("Exception when calling TenantsApi->delete_tenant: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  |

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Tenant deleted successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_tenant**
>
> Tenant get_tenant(tenant_id)

Get tenant by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.tenant import Tenant
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
    api_instance = aivo_sdk.TenantsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 

    try:
        # Get tenant by ID
        api_response = api_instance.get_tenant(tenant_id)
        print("The response of TenantsApi->get_tenant:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantsApi->get_tenant: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  |

### Return type

[**Tenant**](Tenant.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Tenant retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_tenants**
>
> ListTenants200Response list_tenants(limit=limit, offset=offset, status=status)

List tenants

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_tenants200_response import ListTenants200Response
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
    api_instance = aivo_sdk.TenantsApi(api_client)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)
    status = 'status_example' # str |  (optional)

    try:
        # List tenants
        api_response = api_instance.list_tenants(limit=limit, offset=offset, status=status)
        print("The response of TenantsApi->list_tenants:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantsApi->list_tenants: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]
 **status** | **str**|  | [optional]

### Return type

[**ListTenants200Response**](ListTenants200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Tenants retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_tenant**
>
> Tenant update_tenant(tenant_id, update_tenant_request)

Update tenant

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.tenant import Tenant
from aivo_sdk.models.update_tenant_request import UpdateTenantRequest
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
    api_instance = aivo_sdk.TenantsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 
    update_tenant_request = aivo_sdk.UpdateTenantRequest() # UpdateTenantRequest | 

    try:
        # Update tenant
        api_response = api_instance.update_tenant(tenant_id, update_tenant_request)
        print("The response of TenantsApi->update_tenant:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TenantsApi->update_tenant: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  |
 **update_tenant_request** | [**UpdateTenantRequest**](UpdateTenantRequest.md)|  |

### Return type

[**Tenant**](Tenant.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Tenant updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Tenant not found |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
