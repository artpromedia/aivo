# BulkEnrollRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**course_id** | **str** |  |
**learner_ids** | **List[str]** |  |
**expires_at** | **datetime** |  | [optional]
**metadata** | **Dict[str, object]** |  | [optional]

## Example

```python
from aivo_sdk.models.bulk_enroll_request import BulkEnrollRequest

# TODO update the JSON string below
json = "{}"
# create an instance of BulkEnrollRequest from a JSON string
bulk_enroll_request_instance = BulkEnrollRequest.from_json(json)
# print the JSON string representation of the object
print(BulkEnrollRequest.to_json())

# convert the object into a dict
bulk_enroll_request_dict = bulk_enroll_request_instance.to_dict()
# create an instance of BulkEnrollRequest from a dict
bulk_enroll_request_from_dict = BulkEnrollRequest.from_dict(bulk_enroll_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
