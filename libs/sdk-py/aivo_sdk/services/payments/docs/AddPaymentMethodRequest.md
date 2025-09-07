# AddPaymentMethodRequest

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tenant_id** | **str** |  |
**type** | **str** |  |
**token** | **str** | Payment method token from payment processor |
**is_default** | **bool** |  | [optional] [default to False]

## Example

```python
from aivo_sdk.models.add_payment_method_request import AddPaymentMethodRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AddPaymentMethodRequest from a JSON string
add_payment_method_request_instance = AddPaymentMethodRequest.from_json(json)
# print the JSON string representation of the object
print(AddPaymentMethodRequest.to_json())

# convert the object into a dict
add_payment_method_request_dict = add_payment_method_request_instance.to_dict()
# create an instance of AddPaymentMethodRequest from a dict
add_payment_method_request_from_dict = AddPaymentMethodRequest.from_dict(add_payment_method_request_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
