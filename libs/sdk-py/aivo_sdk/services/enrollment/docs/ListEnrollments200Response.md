# ListEnrollments200Response

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[Enrollment]**](Enrollment.md) |  |
**total** | **int** |  |
**limit** | **int** |  |
**offset** | **int** |  |

## Example

```python
from aivo_sdk.models.list_enrollments200_response import ListEnrollments200Response

# TODO update the JSON string below
json = "{}"
# create an instance of ListEnrollments200Response from a JSON string
list_enrollments200_response_instance = ListEnrollments200Response.from_json(json)
# print the JSON string representation of the object
print(ListEnrollments200Response.to_json())

# convert the object into a dict
list_enrollments200_response_dict = list_enrollments200_response_instance.to_dict()
# create an instance of ListEnrollments200Response from a dict
list_enrollments200_response_from_dict = ListEnrollments200Response.from_dict(list_enrollments200_response_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
