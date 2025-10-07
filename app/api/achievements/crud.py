from datetime import datetime, time
from typing import List, Optional

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.achievements import models, schemas
from app.api.base_crud import CRUDBase
from app.api.citizens import models as citizen_models
from app.core.config import settings
from app.core.logger import logger
from app.core.security import SYSTEM_TOKEN, TokenData
from app.core.utils import current_time

MAX_ACHIEVEMENTS_PER_DAY = 3


class CRUDAchievement(
    CRUDBase[models.Achievement, schemas.AchievementCreate, schemas.AchievementCreate]
):
    def create(
        self,
        db: Session,
        obj: schemas.AchievementCreate,
        user: TokenData,
    ) -> models.Achievement:
        """Create a new achievement with automatic sent_at timestamp"""
        # Add the sent_at timestamp and sender_id from user token
        obj_data = obj.model_dump()
        obj_data['sent_at'] = current_time()
        obj_data['sender_id'] = user.citizen_id
        if obj_data['message'] and len(obj_data['message']) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Message must be less than 100 characters',
            )

        today_start = datetime.combine(obj_data['sent_at'].date(), time.min)
        today_end = datetime.combine(obj_data['sent_at'].date(), time.max)

        current_achievements = self.find(
            db=db,
            user=user,
            filters=schemas.AchievementFilter(
                sender_id=obj_data['sender_id'],
                sent_at_from=today_start,
                sent_at_to=today_end,
            ),
        )

        if len(current_achievements) >= MAX_ACHIEVEMENTS_PER_DAY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='You have reached the maximum number of achievements per day',
            )

        # Use the base class create method with AchievementBase schema
        # This includes sender_id from user token and all required fields
        achievement = super().create(db=db, obj=schemas.AchievementBase(**obj_data))

        receiver_id = int(obj_data['receiver_id'])
        sender_id = int(obj_data['sender_id'])
        receiver_citizen = (
            db.query(citizen_models.Citizen)
            .filter(citizen_models.Citizen.id == receiver_id)
            .first()
        )
        sender_citizen = (
            db.query(citizen_models.Citizen)
            .filter(citizen_models.Citizen.id == sender_id)
            .first()
        )

        if receiver_citizen and receiver_citizen.world_address:
            self.send_world_app_notification(
                db=db,
                reciever_adress=receiver_citizen.world_address,
                receiver=receiver_citizen,
                sender=sender_citizen,
            )
        else:
            logger.info('No citizen found or no world_address')

        return achievement

    def _check_permission(self, db_obj: models.Achievement, user: TokenData) -> bool:
        """Check if user can access this achievement"""
        return user == SYSTEM_TOKEN

    def find(
        self,
        db: Session,
        user: TokenData,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[schemas.AchievementFilter] = None,
        sort_by: str = 'sent_at',
        sort_order: str = 'desc',
    ) -> List[models.Achievement]:
        """Get achievements with filtering"""

        citizen_id = user.citizen_id

        # Get sent achievements with receiver citizen data
        sent_achievements_with_citizens = (
            db.query(self.model, citizen_models.Citizen)
            .join(
                citizen_models.Citizen,
                self.model.receiver_id == citizen_models.Citizen.id,
            )
            .filter(self.model.sender_id == citizen_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Get received achievements with sender citizen data
        received_achievements_with_citizens = (
            db.query(self.model, citizen_models.Citizen)
            .join(
                citizen_models.Citizen,
                self.model.sender_id == citizen_models.Citizen.id,
            )
            .filter(self.model.receiver_id == citizen_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Structure the sent achievements data to include receiver info
        sent_achievements = []
        for achievement, citizen in sent_achievements_with_citizens:
            achievement_dict = {
                'achievement': achievement,
                'citizen': {
                    'id': citizen.id,
                    'first_name': citizen.first_name,
                    'last_name': citizen.last_name,
                    'primary_email': citizen.primary_email,
                    'world_address': citizen.world_address,
                },
            }
            sent_achievements.append(achievement_dict)

        # Structure the received achievements data to include sender info
        received_achievements = []
        for achievement, citizen in received_achievements_with_citizens:
            achievement_dict = {
                'achievement': achievement,
                'citizen': {
                    'id': citizen.id,
                    'first_name': citizen.first_name,
                    'last_name': citizen.last_name,
                    'primary_email': citizen.primary_email,
                    'world_address': citizen.world_address,
                },
            }
            received_achievements.append(achievement_dict)

        query = {
            'sent_achievements': sent_achievements,
            'received_achievements': received_achievements,
        }

        return query

    def get_by_receiver(
        self, db: Session, receiver_id: int, user: Optional[TokenData] = None
    ) -> List[models.Achievement]:
        """Get all achievements for a specific receiver application"""
        query = db.query(self.model).filter(self.model.receiver_id == receiver_id)
        return query.order_by(self.model.sent_at.desc()).all()

    def get_by_sender(
        self, db: Session, sender_id: int, user: Optional[TokenData] = None
    ) -> List[models.Achievement]:
        """Get all achievements sent by a specific application"""
        query = db.query(self.model).filter(self.model.sender_id == sender_id)
        return query.order_by(self.model.sent_at.desc()).all()

    def send_world_app_notification(
        self,
        db: Session,
        reciever_adress: str,
        receiver: citizen_models.Citizen,
        sender: citizen_models.Citizen,
    ) -> bool:
        """Send a notification to the world app"""
        logger.info('Sending notification to %s', reciever_adress)
        # Send a notification to the world app
        url = 'https://developer.worldcoin.org/api/v2/minikit/send-notification'
        headers = {
            'Authorization': f'Bearer {settings.WORLD_EDGE_APP_TOKEN}',
            'Content-Type': 'application/json',
        }
        data = {
            'app_id': settings.WORLD_EDGE_APP_ID,
            'wallet_addresses': [reciever_adress],
            'mini_app_path': f'worldapp://mini-app?app_id={settings.WORLD_EDGE_APP_ID}',
            'localisations': [
                {
                    'language': 'en',
                    'title': f'{sender.first_name} sent you a star',
                    'message': f'{sender.first_name} {sender.last_name} has sent you an achievement!',
                }
            ],
        }
        response = requests.post(url, headers=headers, json=data)
        logger.info('Notification sent to %s', response.json())
        return response.json()


achievement = CRUDAchievement(models.Achievement)
