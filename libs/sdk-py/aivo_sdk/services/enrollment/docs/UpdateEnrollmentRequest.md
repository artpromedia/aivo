# UpdateEnrollmentRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **str** |  | [optional]
**expires_at** | **datetime** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.update_enrollment_request import UpdateEnrollmentRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateEnrollmentRequest from a JSON string
update_enrollment_request_instance = UpdateEnrollmentRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateEnrollmentRequest.to_json())

# convert the object into a dict
update_enrollment_request_dict = update_enrollment_request_instance.to_dict()
# create an instance of UpdateEnrollmentRequest from a dict
update_enrollment_request_from_dict = UpdateEnrollmentRequest.from_dict(update_enrollment_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
