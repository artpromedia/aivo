# SubscriptionDetailsRenewal

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**next_billing_date** | **date** |  |
**amount** | **float** | Next billing amount |
**currency** | **str** |  | [optional]
**auto_renew** | **bool** |  |
**days_until_renewal** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.subscription_details_renewal import SubscriptionDetailsRenewal

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsRenewal from a JSON string
subscription_details_renewal_instance = SubscriptionDetailsRenewal.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsRenewal.to_json())

# convert the object into a dict
subscription_details_renewal_dict = subscription_details_renewal_instance.to_dict()
# create an instance of SubscriptionDetailsRenewal from a dict
subscription_details_renewal_from_dict = SubscriptionDetailsRenewal.from_dict(subscription_details_renewal_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
