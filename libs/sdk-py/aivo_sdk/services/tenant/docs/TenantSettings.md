# TenantSettings

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**features** | [**TenantSettingsFeatures**](TenantSettingsFeatures.md) |  |
**branding** | [**TenantSettingsBranding**](TenantSettingsBranding.md) |  |
**notifications** | [**TenantSettingsNotifications**](TenantSettingsNotifications.md) |  |

## Example

```python
from aivo_sdk.models.tenant_settings import TenantSettings

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSettings from a JSON string
tenant_settings_instance = TenantSettings.from_json(json)
# print the JSON string representation of the object
print(TenantSettings.to_json())

# convert the object into a dict
tenant_settings_dict = tenant_settings_instance.to_dict()
# create an instance of TenantSettings from a dict
tenant_settings_from_dict = TenantSettings.from_dict(tenant_settings_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
