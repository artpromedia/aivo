# CreateCouponRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **str** |  | 
**name** | **str** |  | [optional] 
**discount_type** | **str** |  | 
**discount_value** | **float** |  | 
**max_redemptions** | **int** |  | [optional] 
**valid_from** | **datetime** |  | [optional] 
**valid_until** | **datetime** |  | [optional] 

## Example

```python
from aivo_sdk.models.create_coupon_request import CreateCouponRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateCouponRequest from a JSON string
create_coupon_request_instance = CreateCouponRequest.from_json(json)
# print the JSON string representation of the object
print(CreateCouponRequest.to_json())

# convert the object into a dict
create_coupon_request_dict = create_coupon_request_instance.to_dict()
# create an instance of CreateCouponRequest from a dict
create_coupon_request_from_dict = CreateCouponRequest.from_dict(create_coupon_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


