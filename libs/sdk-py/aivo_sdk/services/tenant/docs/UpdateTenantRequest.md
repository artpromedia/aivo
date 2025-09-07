# UpdateTenantRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | [optional]
**description** | **str** |  | [optional]
**logo** | **str** |  | [optional]
**website** | **str** |  | [optional]
**status** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.update_tenant_request import UpdateTenantRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpdateTenantRequest from a JSON string
update_tenant_request_instance = UpdateTenantRequest.from_json(json)
# print the JSON string representation of the object
print(UpdateTenantRequest.to_json())

# convert the object into a dict
update_tenant_request_dict = update_tenant_request_instance.to_dict()
# create an instance of UpdateTenantRequest from a dict
update_tenant_request_from_dict = UpdateTenantRequest.from_dict(update_tenant_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
