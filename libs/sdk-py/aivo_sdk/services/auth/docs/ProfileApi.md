# aivo_sdk.ProfileApi

All URIs are relative to *https://api.aivo.com/auth/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_current_user**](ProfileApi.md#get_current_user) | **GET** /me | Get current user profile


# **get_current_user**
> User get_current_user()

Get current user profile

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.user import User
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/auth/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/auth/v1"
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
    api_instance = aivo_sdk.ProfileApi(api_client)

    try:
        # Get current user profile
        api_response = api_instance.get_current_user()
        print("The response of ProfileApi->get_current_user:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ProfileApi->get_current_user: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**User**](User.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | User profile retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

