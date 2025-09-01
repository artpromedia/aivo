# Invoice


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**subscription_id** | **str** |  | 
**tenant_id** | **str** |  | 
**invoice_number** | **str** |  | [optional] 
**status** | **str** |  | 
**amount_due** | **int** | Amount in cents | 
**amount_paid** | **int** | Amount in cents | 
**currency** | **str** |  | 
**due_date** | **datetime** |  | 
**paid_at** | **datetime** |  | [optional] 
**period_start** | **datetime** |  | [optional] 
**period_end** | **datetime** |  | [optional] 
**download_url** | **str** |  | [optional] 
**line_items** | [**List[InvoiceLineItem]**](InvoiceLineItem.md) |  | [optional] 
**created_at** | **datetime** |  | 

## Example

```python
from aivo_sdk.models.invoice import Invoice

# TODO update the JSON string below
json = "{}"
# create an instance of Invoice from a JSON string
invoice_instance = Invoice.from_json(json)
# print the JSON string representation of the object
print(Invoice.to_json())

# convert the object into a dict
invoice_dict = invoice_instance.to_dict()
# create an instance of Invoice from a dict
invoice_from_dict = Invoice.from_dict(invoice_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


