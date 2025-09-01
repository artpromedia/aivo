# BillingHistoryWebhooksStatus


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**is_configured** | **bool** | Whether webhooks are configured | 
**last_success** | **datetime** | Last successful webhook delivery | 
**failure_count** | **int** | Number of recent webhook failures | 
**endpoint** | **str** | Configured webhook endpoint | [optional] 

## Example

```python
from aivo_sdk.models.billing_history_webhooks_status import BillingHistoryWebhooksStatus

# TODO update the JSON string below
json = "{}"
# create an instance of BillingHistoryWebhooksStatus from a JSON string
billing_history_webhooks_status_instance = BillingHistoryWebhooksStatus.from_json(json)
# print the JSON string representation of the object
print(BillingHistoryWebhooksStatus.to_json())

# convert the object into a dict
billing_history_webhooks_status_dict = billing_history_webhooks_status_instance.to_dict()
# create an instance of BillingHistoryWebhooksStatus from a dict
billing_history_webhooks_status_from_dict = BillingHistoryWebhooksStatus.from_dict(billing_history_webhooks_status_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


