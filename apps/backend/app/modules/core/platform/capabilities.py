from pydantic import BaseModel
from typing import List

class ActionDef(BaseModel):
    code: str
    name: str

class PageDef(BaseModel):
    code: str
    name: str
    actions: List[ActionDef]

class ModuleDef(BaseModel):
    code: str
    name: str
    pages: List[PageDef]

class AppDef(BaseModel):
    code: str
    name: str
    modules: List[ModuleDef]

# The Canonical Capability Registry
# This is the authoritative source of truth for all TMS capabilities.
TMS_CAPABILITY_REGISTRY = AppDef(
    code="tms",
    name="Zolexora TMS",
    modules=[
        ModuleDef(
            code="operations",
            name="Operations",
            pages=[
                PageDef(
                    code="routes",
                    name="Routes",
                    actions=[
                        ActionDef(code="view", name="View Routes"),
                        ActionDef(code="create", name="Create Route"),
                        ActionDef(code="edit", name="Edit Route"),
                        ActionDef(code="cancel", name="Cancel Route"),
                    ]
                ),
                PageDef(
                    code="bookings",
                    name="Bookings",
                    actions=[
                        ActionDef(code="view", name="View Bookings"),
                        ActionDef(code="create", name="Create Booking"),
                        ActionDef(code="edit", name="Edit Booking"),
                        ActionDef(code="cancel", name="Cancel Booking"),
                    ]
                ),
                PageDef(
                    code="dispatch",
                    name="Dispatch",
                    actions=[
                        ActionDef(code="view", name="View Dispatch"),
                        ActionDef(code="assign", name="Assign Resources"),
                    ]
                ),
                PageDef(
                    code="duties",
                    name="Duties",
                    actions=[
                        ActionDef(code="view", name="View Duties"),
                        ActionDef(code="edit", name="Update Duty Status"),
                    ]
                )
            ]
        ),
        ModuleDef(
            code="fleet",
            name="Fleet",
            pages=[
                PageDef(
                    code="vehicles",
                    name="Vehicles",
                    actions=[
                        ActionDef(code="view", name="View Vehicles"),
                        ActionDef(code="create", name="Add Vehicle"),
                        ActionDef(code="edit", name="Edit Vehicle"),
                    ]
                ),
                PageDef(
                    code="drivers",
                    name="Drivers",
                    actions=[
                        ActionDef(code="view", name="View Drivers"),
                        ActionDef(code="create", name="Add Driver"),
                        ActionDef(code="edit", name="Edit Driver"),
                    ]
                )
            ]
        ),
        ModuleDef(
            code="crm",
            name="Organizational TMS Data",
            pages=[
                PageDef(
                    code="operating_units",
                    name="Operating Units",
                    actions=[
                        ActionDef(code="view", name="View OUs"),
                        ActionDef(code="create", name="Add OU"),
                        ActionDef(code="edit", name="Edit OU"),
                    ]
                ),
                PageDef(
                    code="clients",
                    name="Clients",
                    actions=[
                        ActionDef(code="view", name="View Clients"),
                        ActionDef(code="create", name="Add Client"),
                        ActionDef(code="edit", name="Edit Client"),
                    ]
                ),
                PageDef(
                    code="vendors",
                    name="Vendors",
                    actions=[
                        ActionDef(code="view", name="View Vendors"),
                        ActionDef(code="create", name="Add Vendor"),
                        ActionDef(code="edit", name="Edit Vendor"),
                    ]
                )
            ]
        ),
        ModuleDef(
            code="finance",
            name="Finance",
            pages=[
                PageDef(
                    code="billing",
                    name="Billing",
                    actions=[
                        ActionDef(code="view", name="View Billing"),
                        ActionDef(code="generate", name="Generate Invoice"),
                    ]
                ),
                PageDef(
                    code="vendor_payments",
                    name="Vendor Payments",
                    actions=[
                        ActionDef(code="view", name="View Vendor Payments"),
                        ActionDef(code="process", name="Process Payment"),
                    ]
                )
            ]
        ),
        ModuleDef(
            code="reports",
            name="Reports",
            pages=[
                PageDef(
                    code="operations",
                    name="Operations Reports",
                    actions=[
                        ActionDef(code="view", name="View Reports"),
                        ActionDef(code="export", name="Export Reports"),
                    ]
                ),
                PageDef(
                    code="finance",
                    name="Finance Reports",
                    actions=[
                        ActionDef(code="view", name="View Reports"),
                        ActionDef(code="export", name="Export Reports"),
                    ]
                )
            ]
        )
    ]
)
