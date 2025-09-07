# aivo_sdk.AuthenticationApi

All URIs are relative to *<https://api.aivo.com/auth/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**login**](AuthenticationApi.md#login) | **POST** /login | Authenticate user
[**logout**](AuthenticationApi.md#logout) | **POST** /logout | Logout user
[**refresh_token**](AuthenticationApi.md#refresh_token) | **POST** /refresh | Refresh access token

# **login**
>
> AuthResponse login(login_request)

Authenticate user

### Example

```python
import aivo_sdk
from aivo_sdk.models.auth_response import AuthResponse
from aivo_sdk.models.login_request import LoginRequest
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/auth/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/auth/v1"
)


# Enter a context with an instance of the API client
with aivo_sdk.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = aivo_sdk.AuthenticationApi(api_client)
    login_request = aivo_sdk.LoginRequest() # LoginRequest | 

    try:
        # Authenticate user
        api_response = api_instance.login(login_request)
        print("The response of AuthenticationApi->login:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationApi->login: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **login_request** | [**LoginRequest**](LoginRequest.md)|  |

### Return type

[**AuthResponse**](AuthResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Authentication successful |  -  |
**401** | Authentication failed |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout**
>
> logout()

Logout user

### Example

- Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
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
    api_instance = aivo_sdk.AuthenticationApi(api_client)

    try:
        # Logout user
        api_instance.logout()
    except Exception as e:
        print("Exception when calling AuthenticationApi->logout: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

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
**204** | Logout successful |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **refresh_token**
>
> AuthResponse refresh_token(refresh_token_request)

Refresh access token

### Example

- Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.auth_response import AuthResponse
from aivo_sdk.models.refresh_token_request import RefreshTokenRequest
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
    api_instance = aivo_sdk.AuthenticationApi(api_client)
    refresh_token_request = aivo_sdk.RefreshTokenRequest() # RefreshTokenRequest | 

    try:
        # Refresh access token
        api_response = api_instance.refresh_token(refresh_token_request)
        print("The response of AuthenticationApi->refresh_token:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AuthenticationApi->refresh_token: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **refresh_token_request** | [**RefreshTokenRequest**](RefreshTokenRequest.md)|  |

### Return type

[**AuthResponse**](AuthResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Token refreshed successfully |  -  |
**401** | Invalid refresh token |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
