# aivo_sdk.EnrollmentsApi

All URIs are relative to *<https://api.aivo.com/enrollment/v1>*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_enrollment**](EnrollmentsApi.md#create_enrollment) | **POST** /enrollments | Create new enrollment
[**delete_enrollment**](EnrollmentsApi.md#delete_enrollment) | **DELETE** /enrollments/{enrollmentId} | Delete enrollment
[**get_enrollment**](EnrollmentsApi.md#get_enrollment) | **GET** /enrollments/{enrollmentId} | Get enrollment by ID
[**list_enrollments**](EnrollmentsApi.md#list_enrollments) | **GET** /enrollments | List enrollments
[**update_enrollment**](EnrollmentsApi.md#update_enrollment) | **PUT** /enrollments/{enrollmentId} | Update enrollment

# **create_enrollment**
>
> Enrollment create_enrollment(create_enrollment_request)

Create new enrollment

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.create_enrollment_request import CreateEnrollmentRequest
from aivo_sdk.models.enrollment import Enrollment
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
    api_instance = aivo_sdk.EnrollmentsApi(api_client)
    create_enrollment_request = aivo_sdk.CreateEnrollmentRequest() # CreateEnrollmentRequest | 

    try:
        # Create new enrollment
        api_response = api_instance.create_enrollment(create_enrollment_request)
        print("The response of EnrollmentsApi->create_enrollment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnrollmentsApi->create_enrollment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_enrollment_request** | [**CreateEnrollmentRequest**](CreateEnrollmentRequest.md)|  |

### Return type

[**Enrollment**](Enrollment.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Enrollment created successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**409** | Enrollment already exists |  -  |
**422** | Validation error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_enrollment**
>
> delete_enrollment(enrollment_id)

Delete enrollment

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
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
    api_instance = aivo_sdk.EnrollmentsApi(api_client)
    enrollment_id = 'enrollment_id_example' # str | 

    try:
        # Delete enrollment
        api_instance.delete_enrollment(enrollment_id)
    except Exception as e:
        print("Exception when calling EnrollmentsApi->delete_enrollment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **enrollment_id** | **str**|  |

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
**204** | Enrollment deleted successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Enrollment not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_enrollment**
>
> Enrollment get_enrollment(enrollment_id)

Get enrollment by ID

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.enrollment import Enrollment
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
    api_instance = aivo_sdk.EnrollmentsApi(api_client)
    enrollment_id = 'enrollment_id_example' # str | 

    try:
        # Get enrollment by ID
        api_response = api_instance.get_enrollment(enrollment_id)
        print("The response of EnrollmentsApi->get_enrollment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnrollmentsApi->get_enrollment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **enrollment_id** | **str**|  |

### Return type

[**Enrollment**](Enrollment.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Enrollment retrieved successfully |  -  |
**401** | Unauthorized |  -  |
**404** | Enrollment not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_enrollments**
>
> ListEnrollments200Response list_enrollments(tenant_id, learner_id=learner_id, course_id=course_id, status=status, limit=limit, offset=offset)

List enrollments

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.list_enrollments200_response import ListEnrollments200Response
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
    api_instance = aivo_sdk.EnrollmentsApi(api_client)
    tenant_id = 'tenant_id_example' # str | 
    learner_id = 'learner_id_example' # str |  (optional)
    course_id = 'course_id_example' # str |  (optional)
    status = 'status_example' # str |  (optional)
    limit = 20 # int |  (optional) (default to 20)
    offset = 0 # int |  (optional) (default to 0)

    try:
        # List enrollments
        api_response = api_instance.list_enrollments(tenant_id, learner_id=learner_id, course_id=course_id, status=status, limit=limit, offset=offset)
        print("The response of EnrollmentsApi->list_enrollments:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnrollmentsApi->list_enrollments: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **tenant_id** | **str**|  |
 **learner_id** | **str**|  | [optional]
 **course_id** | **str**|  | [optional]
 **status** | **str**|  | [optional]
 **limit** | **int**|  | [optional] [default to 20]
 **offset** | **int**|  | [optional] [default to 0]

### Return type

[**ListEnrollments200Response**](ListEnrollments200Response.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: Not defined
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Enrollments retrieved successfully |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_enrollment**
>
> Enrollment update_enrollment(enrollment_id, update_enrollment_request)

Update enrollment

### Example

* Bearer (JWT) Authentication (bearerAuth):

```python
import aivo_sdk
from aivo_sdk.models.enrollment import Enrollment
from aivo_sdk.models.update_enrollment_request import UpdateEnrollmentRequest
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
    api_instance = aivo_sdk.EnrollmentsApi(api_client)
    enrollment_id = 'enrollment_id_example' # str | 
    update_enrollment_request = aivo_sdk.UpdateEnrollmentRequest() # UpdateEnrollmentRequest | 

    try:
        # Update enrollment
        api_response = api_instance.update_enrollment(enrollment_id, update_enrollment_request)
        print("The response of EnrollmentsApi->update_enrollment:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling EnrollmentsApi->update_enrollment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **enrollment_id** | **str**|  |
 **update_enrollment_request** | [**UpdateEnrollmentRequest**](UpdateEnrollmentRequest.md)|  |

### Return type

[**Enrollment**](Enrollment.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

* **Content-Type**: application/json
* **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Enrollment updated successfully |  -  |
**400** | Bad request |  -  |
**401** | Unauthorized |  -  |
**404** | Enrollment not found |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
