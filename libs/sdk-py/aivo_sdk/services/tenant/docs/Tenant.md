# Tenant

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  |
**name** | **str** |  |
**slug** | **str** |  |
**description** | **str** |  | [optional]
**logo** | **str** |  | [optional]
**website** | **str** |  | [optional]
**status** | **str** |  |
**plan** | **str** |  |
**max_users** | **int** |  | [optional]
**max_seats** | **int** |  | [optional]
**trial_ends_at** | **datetime** |  | [optional]
**created_at** | **datetime** |  |
**updated_at** | **datetime** |  |

## Example

```python
from aivo_sdk.models.tenant import Tenant

# TODO update the JSON string below
json = "{}"
# create an instance of Tenant from a JSON string
tenant_instance = Tenant.from_json(json)
# print the JSON string representation of the object
print(Tenant.to_json())

# convert the object into a dict
tenant_dict = tenant_instance.to_dict()
# create an instance of Tenant from a dict
tenant_from_dict = Tenant.from_dict(tenant_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
