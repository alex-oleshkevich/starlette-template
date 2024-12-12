import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.sqla.columns import AutoCreatedAt, DateTimeTz, IntPk
from app.config.sqla.models import Base
from app.contexts.users.models import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (sa.Index("refresh_tokens_jit_udx", "jit", unique=True),)
    id: Mapped[IntPk]
    jit: Mapped[str] = mapped_column()
    expires_at: Mapped[DateTimeTz] = mapped_column()
    created_at: Mapped[AutoCreatedAt]
    user_id: Mapped[int] = mapped_column(sa.ForeignKey(User.id))

    user: Mapped[User] = relationship(User)
