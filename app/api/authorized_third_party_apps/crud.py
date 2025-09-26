from typing import Optional

from sqlalchemy.orm import Session

from app.api.authorized_third_party_apps import models, schemas
from app.api.base_crud import CRUDBase
from app.core.security import TokenData


class CRUDAuthorizedThirdPartyApp(
    CRUDBase[
        models.AuthorizedThirdPartyApp,
        schemas.AuthorizedThirdPartyAppCreate,
        schemas.AuthorizedThirdPartyAppUpdate,
    ]
):
    def _check_permission(
        self, db_obj: models.AuthorizedThirdPartyApp, user: TokenData
    ) -> bool:
        return True

    def get_by_api_key(
        self, db: Session, api_key: str
    ) -> Optional[models.AuthorizedThirdPartyApp]:
        """Get a third party app by API key"""
        return (
            db.query(self.model)
            .filter(self.model.api_key == api_key)
            .filter(self.model.active.is_(True))
            .first()
        )


authorized_third_party_app = CRUDAuthorizedThirdPartyApp(models.AuthorizedThirdPartyApp)
