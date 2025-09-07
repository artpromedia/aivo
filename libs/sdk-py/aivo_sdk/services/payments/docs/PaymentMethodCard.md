# PaymentMethodCard

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**brand** | **str** |  | [optional]
**last4** | **str** |  | [optional]
**exp_month** | **int** |  | [optional]
**exp_year** | **int** |  | [optional]

## Example

```python
from aivo_sdk.models.payment_method_card import PaymentMethodCard

# TODO update the JSON string below
json = "{}"
# create an instance of PaymentMethodCard from a JSON string
payment_method_card_instance = PaymentMethodCard.from_json(json)
# print the JSON string representation of the object
print(PaymentMethodCard.to_json())

# convert the object into a dict
payment_method_card_dict = payment_method_card_instance.to_dict()
# create an instance of PaymentMethodCard from a dict
payment_method_card_from_dict = PaymentMethodCard.from_dict(payment_method_card_dict)
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
