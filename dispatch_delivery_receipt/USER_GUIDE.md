# Dispatch Delivery Receipt – Step-by-Step Guide

For warehouse associates, supervisors and team leaders who prepare the DDR sheet for a delivery run.

## A. One-time setup (Admin)

1. Turn on Developer Mode: Settings → Activate developer mode.
2. Apps → Update Apps List → Update.
3. Search **Dispatch Delivery Receipt** → Install (requires Inventory, Sales, Fleet).
4. Update existing installs with Apps → Dispatch Delivery Receipt → Upgrade.

## B. Master data to prepare

### Customers (Contacts)
1. Open the customer's **delivery address**.
2. Fill in **City** (and Province). The Location column on the sheet comes from City.
3. Use the same spelling for every customer in the same area (e.g. always `Dagupan City`).

### Fleet (Fleet app)
1. Open each truck under Fleet → Vehicles.
2. Fill in **License Plate**, **Model**, **Driver** and keep the **Odometer** log updated.
3. Third-party trucks and drivers (e.g. Transportify) can be skipped; type them in manually on the dispatch.

## C. Creating a dispatch (per delivery run)

### Step 1 – Select the delivery orders
1. Inventory → Operations → **Deliveries**.
2. Tick all delivery orders that go on the same truck.
3. Click **Actions (gear)** → **Create Dispatch Receipt**.

> Alternative: Inventory → Warehouse Management → **Dispatch Receipts** → **New**, then add delivery orders on the Deliveries tab.

### Step 2 – Pick the truck or driver
- Select the **Vehicle**: Driver's Name, Driver Contact, Plate No., Truck Model, Truck Type and Odometer (Departure) fill in automatically.
- Or select the **Driver** first: the vehicle assigned to that driver is picked for you.
- Third-party truck/driver: type the Driver's Name, Plate No. and Truck Model directly.

### Step 3 – Complete the header
| Field | Notes |
|---|---|
| Delivery Date | Defaults to today; change if needed |
| Delivery Helper(s) | Free text, e.g. `Rico Escandor / Daryll Sol Pacay` |
| Transport Provider | Printed under the Control # |
| Delivery Area | Auto-built from line locations; editable |
| Signatories tab | Prepared By, Approved By, Dispatched By |

The **Control #** (format `MMYY-###`, e.g. `1126-017`) is generated on save.

### Step 4 – Review the lines (Deliveries tab)
| Column | Source |
|---|---|
| TR/DR# | Delivery order name |
| SI# | Linked sale order reference |
| Location | Customer city, normalized so the same area always reads identically |
| Client Name | Customer on the delivery order |
| Remarks | Optional, typed in |

Any of these can be corrected on the line. A delivery order can be on only one active dispatch.

### Step 5 – Print
1. Click **Print DDR**.
2. The landscape PDF lists stops sorted by Location, so same-area drops are together.
3. Time In/Out, ASR#, Signature and Odometer (Arrival) are left blank for the driver to fill in.

### Step 6 – Release the truck
1. Click **Dispatch** when the truck leaves (state: Dispatched).
2. After the run, type the **Odometer (Arrival)** and click **Mark Done**.

### Cancel or change
- **Cancel** frees the delivery orders for another dispatch.
- **Set to Draft** lets you edit a cancelled dispatch again.

## D. Troubleshooting

| Problem | Fix |
|---|---|
| Location blank or different spelling | Fix City on the customer's delivery address, or overwrite Location on the line |
| Delivery order cannot be selected | Only outgoing deliveries that are not Draft or Cancelled are allowed |
| "Already on dispatch …" error | Cancel the other dispatch or remove the line there first |
| SI# blank | The delivery has no linked sale order; type it on the line |
| Driver/truck fields blank | The vehicle has no Driver/Plate in Fleet; fill in Fleet or type manually |
| No "Create Dispatch Receipt" action | Refresh the browser and make sure you are in the Deliveries list |
