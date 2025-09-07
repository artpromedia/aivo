# aivo_sdk.BulkOperationsApi

All URIs are relative to *<https://api.aivo.com/enrollment/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**bulk_enroll**](BulkOperationsApi.md#bulk_enroll) | **POST** /bulk-enroll | Bulk enroll learners

# **bulk_enroll**
>
> BulkEnrollResponse bulk_enroll(bulk_enroll_request)

Bulk enroll learners

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.bulk_enroll_request import BulkEnrollRequest
from aivo_sdk.models.bulk_enroll_response import BulkEnrollResponse
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/enrollment/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/enrollment/v1"
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
    api_instance = aivo_sdk.BulkOperationsApi(api_client)
    bulk_enroll_request = aivo_sdk.BulkEnrollRequest() # BulkEnrollRequest | 

    try:
        # Bulk enroll learners
        api_response = api_instance.bulk_enroll(bulk_enroll_request)
        print("The response of BulkOperationsApi->bulk_enroll:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BulkOperationsApi->bulk_enroll: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bulk_enroll_request** | [**BulkEnrollRequest**](BulkEnrollRequest.md)|  |

### Return type

[**BulkEnrollResponse**](BulkEnrollResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Bulk enrollment completed |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
