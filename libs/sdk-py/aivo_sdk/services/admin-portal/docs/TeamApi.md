# aivo_sdk.TeamApi

All URIs are relative to *<https://api.aivo.com/admin/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_tenant_team**](TeamApi.md#get_tenant_team) | **GET** /team | Get tenant team overview

# **get_tenant_team**
>
> TeamOverview get_tenant_team(tenant_id)

Get tenant team overview

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.team_overview import TeamOverview
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
    api_instance = aivo_sdk.TeamApi(api_client)
    tenant_id = '456e7890-e89b-12d3-a456-426614174000' # str | Tenant ID to get team overview for

    try:
        # Get tenant team overview
        api_response = api_instance.get_tenant_team(tenant_id)
        print("The response of TeamApi->get_tenant_team:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling TeamApi->get_tenant_team: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**| Tenant ID to get team overview for |

### Return type

[**TeamOverview**](TeamOverview.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Team overview retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**403** | Forbidden - insufficient permissions |  -  |
**404** | Tenant not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
