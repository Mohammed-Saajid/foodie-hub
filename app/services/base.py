from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.order_repository import OrderRepository
from app.repositories.support_repository import ReportRepository
from app.repositories.terms_and_conditions_repository import TermsAndConditionsRepository
from app.repositories.user_repository import UserRepository


class BaseService:
    def __init__(
        self,
        db: AsyncSession,
        order_repository: OrderRepository,
        report_repository: ReportRepository,
        user_repository: UserRepository,
        terms_repository: TermsAndConditionsRepository,
    ):
        self.db = db
        self.order_repository = order_repository
        self.report_repository = report_repository
        self.user_repository = user_repository
        self.terms_repository = terms_repository
