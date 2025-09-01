# Coupon


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**code** | **str** |  | 
**name** | **str** |  | [optional] 
**discount_type** | **str** |  | 
**discount_value** | **float** |  | 
**max_redemptions** | **int** |  | [optional] 
**redemptions** | **int** |  | [optional] 
**valid_from** | **datetime** |  | [optional] 
**valid_until** | **datetime** |  | [optional] 
**active** | **bool** |  | 
**created_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.coupon import Coupon

# TODO update the JSON string below
json = "{}"
# create an instance of Coupon from a JSON string
coupon_instance = Coupon.from_json(json)
# print the JSON string representation of the object
print(Coupon.to_json())

# convert the object into a dict
coupon_dict = coupon_instance.to_dict()
# create an instance of Coupon from a dict
coupon_from_dict = Coupon.from_dict(coupon_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


