from sqlalchemy import BigInteger, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.connection import Base

class GuildAdminRole(Base):
    __tablename__ = "guild_admin_roles"

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

class GuildPermissionRole(Base):
    __tablename__ = "guild_permission_roles"
    __table_args__ = (
        UniqueConstraint("guild_id", "permission_type", "role_id", name="uq_guild_perm_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.guild_id", ondelete="CASCADE"), nullable=False, index=True)
    permission_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
