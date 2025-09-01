# ListAssessments200Response


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**data** | [**List[Assessment]**](Assessment.md) |  | 
**total** | **int** |  | 
**limit** | **int** |  | 
**offset** | **int** |  | 

## Example

```python
from aivo_sdk.models.list_assessments200_response import ListAssessments200Response

# TODO update the JSON string below
json = "{}"
# create an instance of ListAssessments200Response from a JSON string
list_assessments200_response_instance = ListAssessments200Response.from_json(json)
# print the JSON string representation of the object
print(ListAssessments200Response.to_json())

# convert the object into a dict
list_assessments200_response_dict = list_assessments200_response_instance.to_dict()
# create an instance of ListAssessments200Response from a dict
list_assessments200_response_from_dict = ListAssessments200Response.from_dict(list_assessments200_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


