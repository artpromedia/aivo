# BulkImportResponse

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**successful** | **int** |  |
**failed** | **int** |  |
**total** | **int** |  |
**errors** | [**List[BulkImportResponseErrorsInner]**](BulkImportResponseErrorsInner.md) |  | [optional]

## Example

```python
from aivo_sdk.models.bulk_import_response import BulkImportResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BulkImportResponse from a JSON string
bulk_import_response_instance = BulkImportResponse.from_json(json)
# print the JSON string representation of the object
print(BulkImportResponse.to_json())

# convert the object into a dict
bulk_import_response_dict = bulk_import_response_instance.to_dict()
# create an instance of BulkImportResponse from a dict
bulk_import_response_from_dict = BulkImportResponse.from_dict(bulk_import_response_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
