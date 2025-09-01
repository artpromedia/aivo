# TenantSettingsBranding


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**primary_color** | **str** |  | [optional] 
**secondary_color** | **str** |  | [optional] 
**logo** | **str** |  | [optional] 
**favicon** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.tenant_settings_branding import TenantSettingsBranding

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSettingsBranding from a JSON string
tenant_settings_branding_instance = TenantSettingsBranding.from_json(json)
# print the JSON string representation of the object
print(TenantSettingsBranding.to_json())

# convert the object into a dict
tenant_settings_branding_dict = tenant_settings_branding_instance.to_dict()
# create an instance of TenantSettingsBranding from a dict
tenant_settings_branding_from_dict = TenantSettingsBranding.from_dict(tenant_settings_branding_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


