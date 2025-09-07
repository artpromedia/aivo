# BulkImportResponseErrorsInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**index** | **int** |  | [optional]
**email** | **str** |  | [optional]
**error** | **str** |  | [optional]
**message** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.bulk_import_response_errors_inner import BulkImportResponseErrorsInner

# TODO update the JSON string below
json = "{}"
# create an instance of BulkImportResponseErrorsInner from a JSON string
bulk_import_response_errors_inner_instance = BulkImportResponseErrorsInner.from_json(json)
# print the JSON string representation of the object
print(BulkImportResponseErrorsInner.to_json())

# convert the object into a dict
bulk_import_response_errors_inner_dict = bulk_import_response_errors_inner_instance.to_dict()
# create an instance of BulkImportResponseErrorsInner from a dict
bulk_import_response_errors_inner_from_dict = BulkImportResponseErrorsInner.from_dict(bulk_import_response_errors_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
