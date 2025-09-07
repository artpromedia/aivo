# BulkEnrollResponseErrorsInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**learner_id** | **str** |  | [optional]
**error** | **str** |  | [optional]
**message** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.bulk_enroll_response_errors_inner import BulkEnrollResponseErrorsInner

# TODO update the JSON string below
json = "{}"
# create an instance of BulkEnrollResponseErrorsInner from a JSON string
bulk_enroll_response_errors_inner_instance = BulkEnrollResponseErrorsInner.from_json(json)
# print the JSON string representation of the object
print(BulkEnrollResponseErrorsInner.to_json())

# convert the object into a dict
bulk_enroll_response_errors_inner_dict = bulk_enroll_response_errors_inner_instance.to_dict()
# create an instance of BulkEnrollResponseErrorsInner from a dict
bulk_enroll_response_errors_inner_from_dict = BulkEnrollResponseErrorsInner.from_dict(bulk_enroll_response_errors_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
