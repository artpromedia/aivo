# SubscriptionDetails


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  | 
**plan** | [**SubscriptionDetailsPlan**](SubscriptionDetailsPlan.md) |  | 
**seats** | [**SubscriptionDetailsSeats**](SubscriptionDetailsSeats.md) |  | 
**renewal** | [**SubscriptionDetailsRenewal**](SubscriptionDetailsRenewal.md) |  | 
**status** | **str** |  | 
**coupons** | [**List[SubscriptionDetailsCouponsInner]**](SubscriptionDetailsCouponsInner.md) |  | [optional] 
**discounts** | [**List[SubscriptionDetailsDiscountsInner]**](SubscriptionDetailsDiscountsInner.md) |  | [optional] 
**trial_info** | [**SubscriptionDetailsTrialInfo**](SubscriptionDetailsTrialInfo.md) |  | [optional] 
**last_updated** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.subscription_details import SubscriptionDetails

# TODO update the JSON string below
json = "{}"
# create an instance of SubscriptionDetails from a JSON string
subscription_details_instance = SubscriptionDetails.from_json(json)
# print the JSON string representation of the object
print(SubscriptionDetails.to_json())

# convert the object into a dict
subscription_details_dict = subscription_details_instance.to_dict()
# create an instance of SubscriptionDetails from a dict
subscription_details_from_dict = SubscriptionDetails.from_dict(subscription_details_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


