from pydantic import BaseModel


class NotificationPreference(BaseModel):
    type: str  # 'late_payment', 'bail_expiring', 'quittance_pending', 'pno_expiring', 'new_loyer', 'new_associe', 'subscription_expiring'
    email_enabled: bool = True
    in_app_enabled: bool = True


class NotificationPreferencesResponse(BaseModel):
    preferences: list[NotificationPreference]


class NotificationPreferencesUpdate(BaseModel):
    preferences: list[NotificationPreference]
