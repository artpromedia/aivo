# PaymentMethodBankAccount


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**bank_name** | **str** |  | [optional] 
**last4** | **str** |  | [optional] 
**account_type** | **str** |  | [optional] 

## Example

```python
from aivo_sdk.models.payment_method_bank_account import PaymentMethodBankAccount

# TODO update the JSON string below
json = "{}"
# create an instance of PaymentMethodBankAccount from a JSON string
payment_method_bank_account_instance = PaymentMethodBankAccount.from_json(json)
# print the JSON string representation of the object
print(PaymentMethodBankAccount.to_json())

# convert the object into a dict
payment_method_bank_account_dict = payment_method_bank_account_instance.to_dict()
# create an instance of PaymentMethodBankAccount from a dict
payment_method_bank_account_from_dict = PaymentMethodBankAccount.from_dict(payment_method_bank_account_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


