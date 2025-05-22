# Import all the models, so that Base has them before being imported by Alembic
from app.db.session import Base
from app.models.user import User
from app.models.payment import Payment
from app.models.video import Video