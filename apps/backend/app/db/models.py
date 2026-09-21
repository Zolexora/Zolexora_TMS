from app.db.base import Base
from app.modules.core.platform.models import (
    TenantDatabaseRegistry,
    OrganisationDatabaseAssignment,
    TenantMongodbRegistry,
    OrganisationMongodbAssignment,
    OrganisationStorageAssignment,
    PlatformAuditLog,
    ProviderType,
    RegistryStatus,
    TenantMigrationJob,
    MigrationStatus
)
from app.modules.identity.organisations.models import Organisation, OrganisationStatus, OrganisationType
from app.modules.identity.users.models import Profile
from app.modules.identity.roles.models import (
    PlatformRoleTemplate,
    PlatformRoleTemplatePermission,
    OrganisationRole,
    OrganisationRoleVersion,
    OrganisationRolePermission,
    RoleAssignment,
    UserPermissionOverride,
    RoleStatus,
    RoleSource,
    OverrideType,
)
from app.modules.identity.organisations.membership_models import OrganisationMember, MemberStatus, OrganisationInvitation

from app.modules.core.customization.models import (
    OrganisationApplication,
    ApplicationType,
    ApplicationStatus,
    ConfigType,
    ApplicationModule,
    ApplicationPage,
    ApplicationAction,
    ApplicationConfiguration,
    ApplicationWorkflow,
    ApplicationRule,
    ApplicationForm,
    ApplicationReport,
    ApplicationApproval
)

from app.modules.operations.operating_units.models import (
    OperatingUnit,
    OperatingUnitLocation,
    OperatingUnitStatus
)

__all__ = [
    "Base",
    "TenantDatabaseRegistry",
    "OrganisationDatabaseAssignment",
    "TenantMongodbRegistry",
    "OrganisationMongodbAssignment",
    "OrganisationStorageAssignment",
    "PlatformAuditLog",
    "ProviderType",
    "RegistryStatus",
    "TenantMigrationJob",
    "MigrationStatus",
    "Organisation",
    "OrganisationStatus",
    "OrganisationType",
    "Profile",
    # Prompt 07: RBAC
    "PlatformRoleTemplate",
    "PlatformRoleTemplatePermission",
    "OrganisationRole",
    "OrganisationRoleVersion",
    "OrganisationRolePermission",
    "RoleAssignment",
    "UserPermissionOverride",
    "RoleStatus",
    "RoleSource",
    "OverrideType",
    # Membership
    "OrganisationMember",
    "MemberStatus",
    "OrganisationInvitation",
    # Customization
    "OrganisationApplication",
    "ApplicationType",
    "ApplicationStatus",
    "ConfigType",
    "ApplicationModule",
    "ApplicationPage",
    "ApplicationAction",
    "ApplicationConfiguration",
    "ApplicationWorkflow",
    "ApplicationRule",
    "ApplicationForm",
    "ApplicationReport",
    "ApplicationApproval",
    "OperatingUnit",
    "OperatingUnitLocation",
    "OperatingUnitStatus"
]

from app.modules.crm.clients.models import Client, ClientLocation, ClientLocationOUHistory, ClientStatus
from app.modules.crm.vendors.models import Vendor, VendorStatus, VendorType

__all__.extend([
    "Client",
    "ClientLocation",
    "ClientLocationOUHistory",
    "ClientStatus",
    "Vendor",
    "VendorStatus",
    "VendorType"
])
