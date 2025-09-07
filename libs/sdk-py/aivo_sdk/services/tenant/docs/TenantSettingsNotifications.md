# TenantSettingsNotifications

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**email_notifications** | **bool** |  | [optional] [default to True]
**slack_webhook** | **str** |  | [optional]
**webhook_url** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.tenant_settings_notifications import TenantSettingsNotifications

# TODO update the JSON string below
json = "{}"
# create an instance of TenantSettingsNotifications from a JSON string
tenant_settings_notifications_instance = TenantSettingsNotifications.from_json(json)
# print the JSON string representation of the object
print(TenantSettingsNotifications.to_json())

# convert the object into a dict
tenant_settings_notifications_dict = tenant_settings_notifications_instance.to_dict()
# create an instance of TenantSettingsNotifications from a dict
tenant_settings_notifications_from_dict = TenantSettingsNotifications.from_dict(tenant_settings_notifications_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
