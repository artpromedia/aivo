# aivo_sdk.AssessmentsApi

All URIs are relative to *<https://api.aivo.com/orchestrator/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_assessments**](AssessmentsApi.md#list_assessments) | **GET** /assessments | List assessments
[**submit_assessment**](AssessmentsApi.md#submit_assessment) | **POST** /assessments/{assessmentId}/submit | Submit assessment

# **list_assessments**
>
> ListAssessments200Response list_assessments(course_id=course_id, module_id=module_id, type=type, limit=limit, offset=offset)

List assessments

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_assessments200_response import ListAssessments200Response
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/orchestrator/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/orchestrator/v1"
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
    api_instance = aivo_sdk.AssessmentsApi(api_client)
    course_id = 'course_id_example' # str |  (optional)
    module_id = 'module_id_example' # str |  (optional)
    type = 'type_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List assessments
        api_response = api_instance.list_assessments(course_id=course_id, module_id=module_id, type=type, limit=limit, offset=offset)
        print("The response of AssessmentsApi->list_assessments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AssessmentsApi->list_assessments: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **course_id** | **str**|  | [optional]
 **module_id** | **str**|  | [optional]
 **type** | **str**|  | [optional]
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListAssessments200Response**](ListAssessments200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Assessments retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **submit_assessment**
>
> AssessmentResult submit_assessment(assessment_id, submit_assessment_request)

Submit assessment

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.assessment_result import AssessmentResult
from aivo_sdk.models.submit_assessment_request import SubmitAssessmentRequest
from aivo_sdk.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.aivo.com/orchestrator/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = aivo_sdk.Configuration(
    host = "https://api.aivo.com/orchestrator/v1"
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
    api_instance = aivo_sdk.AssessmentsApi(api_client)
    assessment_id = 'assessment_id_example' # str | 
    submit_assessment_request = aivo_sdk.SubmitAssessmentRequest() # SubmitAssessmentRequest | 

    try:
        # Submit assessment
        api_response = api_instance.submit_assessment(assessment_id, submit_assessment_request)
        print("The response of AssessmentsApi->submit_assessment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling AssessmentsApi->submit_assessment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **assessment_id** | **str**|  |
 **submit_assessment_request** | [**SubmitAssessmentRequest**](SubmitAssessmentRequest.md)|  |

### Return type

[**AssessmentResult**](AssessmentResult.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Assessment submitted successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Assessment not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
