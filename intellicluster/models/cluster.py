"""
Cluster ORM entity representing a group of compute nodes and managed workloads.
"""

from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from intellicluster.core.constants import ClusterStatus
from intellicluster.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from intellicluster.models.node import Node
    from intellicluster.models.workload import Workload


class Cluster(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cluster database model."""

    __tablename__ = "clusters"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=ClusterStatus.ACTIVE.value,
        nullable=False,
    )

    # Relationships
    nodes: Mapped[list["Node"]] = relationship(
        "Node",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    workloads: Mapped[list["Workload"]] = relationship(
        "Workload",
        back_populates="cluster",
    )

    def __repr__(self) -> str:
        return f"<Cluster(id='{self.id}', name='{self.name}', status='{self.status}')>"
