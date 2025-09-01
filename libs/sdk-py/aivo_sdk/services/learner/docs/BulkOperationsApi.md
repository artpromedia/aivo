# aivo_sdk.BulkOperationsApi

All URIs are relative to *https://api.aivo.com/learner/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**bulk_import_learners**](BulkOperationsApi.md#bulk_import_learners) | **POST** /bulk-import | Bulk import learners


# **bulk_import_learners**
> BulkImportResponse bulk_import_learners(bulk_import_request)

Bulk import learners

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.bulk_import_request import BulkImportRequest
from aivo_sdk.models.bulk_import_response import BulkImportResponse
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/learner/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/learner/v1"
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
    bulk_import_request = aivo_sdk.BulkImportRequest() # BulkImportRequest | 

    try:
        # Bulk import learners
        api_response = api_instance.bulk_import_learners(bulk_import_request)
        print("The response of BulkOperationsApi->bulk_import_learners:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling BulkOperationsApi->bulk_import_learners: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **bulk_import_request** | [**BulkImportRequest**](BulkImportRequest.md)|  | 

### Return type

[**BulkImportResponse**](BulkImportResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Bulk import completed |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

