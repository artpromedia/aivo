# BulkEnrollResponse

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**successful** | **int** |  |
**failed** | **int** |  |
**total** | **int** |  |
**errors** | [**List[BulkEnrollResponseErrorsInner]**](BulkEnrollResponseErrorsInner.md) |  | [optional]

## Example

```python
from aivo_sdk.models.bulk_enroll_response import BulkEnrollResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BulkEnrollResponse from a JSON string
bulk_enroll_response_instance = BulkEnrollResponse.from_json(json)
# print the JSON string representation of the object
print(BulkEnrollResponse.to_json())

# convert the object into a dict
bulk_enroll_response_dict = bulk_enroll_response_instance.to_dict()
# create an instance of BulkEnrollResponse from a dict
bulk_enroll_response_from_dict = BulkEnrollResponse.from_dict(bulk_enroll_response_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
