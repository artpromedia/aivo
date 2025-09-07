# SubscriptionDetailsCouponsInner

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **str** |  | [optional]
**discount** | **str** |  | [optional]
**valid_until** | **date** |  | [optional]
**status** | **str** |  | [optional]

## Example

```python
from aivo_sdk.models.subscription_details_coupons_inner import SubscriptionDetailsCouponsInner

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetailsCouponsInner from a JSON string
subscription_details_coupons_inner_instance = SubscriptionDetailsCouponsInner.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetailsCouponsInner.to_json())

# convert the object into a dict
subscription_details_coupons_inner_dict = subscription_details_coupons_inner_instance.to_dict()
# create an instance of SubscriptionDetailsCouponsInner from a dict
subscription_details_coupons_inner_from_dict = SubscriptionDetailsCouponsInner.from_dict(subscription_details_coupons_inner_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
