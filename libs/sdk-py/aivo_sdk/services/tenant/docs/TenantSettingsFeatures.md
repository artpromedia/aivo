# TenantSettingsFeatures

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**enable_sso** | **bool** |  | [optional] [default to False]
**enable_api** | **bool** |  | [optional] [default to True]
**enable_reporting** | **bool** |  | [optional] [default to True]
**enable_custom_branding** | **bool** |  | [optional] [default to False]

## Example

```python
from aivo_sdk.models.tenant_settings_features import TenantSettingsFeatures

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSettingsFeatures from a JSON string
tenant_settings_features_instance = TenantSettingsFeatures.from_json(json)
# print the JSON string representation of the object
print(TenantSettingsFeatures.to_json())

# convert the object into a dict
tenant_settings_features_dict = tenant_settings_features_instance.to_dict()
# create an instance of TenantSettingsFeatures from a dict
tenant_settings_features_from_dict = TenantSettingsFeatures.from_dict(tenant_settings_features_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
