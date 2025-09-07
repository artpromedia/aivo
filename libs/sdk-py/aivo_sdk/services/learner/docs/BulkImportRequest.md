# BulkImportRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**learners** | [**List[CreateLearnerRequest]**](CreateLearnerRequest.md) |  |

## Example

```python
from aivo_sdk.models.bulk_import_request import BulkImportRequest

# TODO update the JSON string below
json = "{}"
# create an instance of BulkImportRequest from a JSON string
bulk_import_request_instance = BulkImportRequest.from_json(json)
# print the JSON string representation of the object
print(BulkImportRequest.to_json())

# convert the object into a dict
bulk_import_request_dict = bulk_import_request_instance.to_dict()
# create an instance of BulkImportRequest from a dict
bulk_import_request_from_dict = BulkImportRequest.from_dict(bulk_import_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
