# CreateEnrollmentRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  | 
**learner_id** | **str** |  | 
**course_id** | **str** |  | 
**expires_at** | **datetime** |  | [optional] 
**metadata** | **Dict[str, object]** |  | [optional] 

## Example

```python
from aivo_sdk.models.create_enrollment_request import CreateEnrollmentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateEnrollmentRequest from a JSON string
create_enrollment_request_instance = CreateEnrollmentRequest.from_json(json)
# print the JSON string representation of the object
print(CreateEnrollmentRequest.to_json())

# convert the object into a dict
create_enrollment_request_dict = create_enrollment_request_instance.to_dict()
# create an instance of CreateEnrollmentRequest from a dict
create_enrollment_request_from_dict = CreateEnrollmentRequest.from_dict(create_enrollment_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


