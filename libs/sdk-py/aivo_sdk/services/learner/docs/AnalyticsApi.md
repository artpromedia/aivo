# aivo_sdk.AnalyticsApi

All URIs are relative to *https://api.aivo.com/learner/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_learner_analytics**](AnalyticsApi.md#get_learner_analytics) | **GET** /learners/{learnerId}/analytics | Get learner analytics


# **get_learner_analytics**
> LearnerAnalytics get_learner_analytics(learner_id, range=range)

Get learner analytics

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.learner_analytics import LearnerAnalytics
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
    api_instance = aivo_sdk.AnalyticsApi(api_client)
    learner_id = 'learner_id_example' # str | 
    range = 30d # str |  (optional) (default to 30d)

    try:
        # Get learner analytics
        api_response = api_instance.get_learner_analytics(learner_id, range=range)
        print("The response of AnalyticsApi->get_learner_analytics:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AnalyticsApi->get_learner_analytics: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **learner_id** | **str**|  | 
 **range** | **str**|  | [optional] [default to 30d]

### Return type

[**LearnerAnalytics**](LearnerAnalytics.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Learner analytics retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Learner not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

