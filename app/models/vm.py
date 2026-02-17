"""VM database model and state definitions."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VMState(str, enum.Enum):
    """VM lifecycle states matching OpenStack server states."""

    # Initial states
    BUILDING = "BUILDING"
    BUILD = "BUILD"

    # Running states
    ACTIVE = "ACTIVE"
    RUNNING = "RUNNING"

    # Stopped states
    STOPPED = "STOPPED"
    SHUTOFF = "SHUTOFF"

    # Transitional states
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    REBOOT = "REBOOT"
    HARD_REBOOT = "HARD_REBOOT"
    RESIZE = "RESIZE"
    VERIFY_RESIZE = "VERIFY_RESIZE"
    MIGRATING = "MIGRATING"

    # Error states
    ERROR = "ERROR"

    # Deleted state
    DELETED = "DELETED"
    SOFT_DELETED = "SOFT_DELETED"

    @classmethod
    def active_states(cls) -> list["VMState"]:
        """Return states considered as 'running'."""
        return [cls.ACTIVE, cls.RUNNING]

    @classmethod
    def stopped_states(cls) -> list["VMState"]:
        """Return states considered as 'stopped'."""
        return [cls.STOPPED, cls.SHUTOFF]

    @classmethod
    def transitional_states(cls) -> list["VMState"]:
        """Return transitional states."""
        return [
            cls.BUILDING,
            cls.BUILD,
            cls.REBOOT,
            cls.HARD_REBOOT,
            cls.RESIZE,
            cls.VERIFY_RESIZE,
            cls.MIGRATING,
        ]


class VM(Base):
    """Virtual Machine database model."""

    __tablename__ = "vms"

    # Primary key - internal database ID
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # VM identifiers
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # OpenStack reference (if synced with real OpenStack)
    openstack_id: Mapped[Optional[str]] = mapped_column(
        String(36), unique=True, nullable=True, index=True
    )

    # VM Configuration
    flavor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    image_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # VM State
    state: Mapped[VMState] = mapped_column(
        Enum(VMState),
        nullable=False,
        default=VMState.BUILDING,
        index=True,
    )
    state_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Network information
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    floating_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Resource specifications (denormalized from flavor for quick access)
    vcpus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    disk_gb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    launched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    terminated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation of VM."""
        return f"<VM(uuid={self.uuid}, name={self.name}, state={self.state})>"

    @property
    def is_running(self) -> bool:
        """Check if VM is in a running state."""
        return self.state in VMState.active_states()

    @property
    def is_stopped(self) -> bool:
        """Check if VM is in a stopped state."""
        return self.state in VMState.stopped_states()

    @property
    def is_transitioning(self) -> bool:
        """Check if VM is in a transitional state."""
        return self.state in VMState.transitional_states()

    @property
    def can_start(self) -> bool:
        """Check if VM can be started."""
        return self.state in VMState.stopped_states()

    @property
    def can_stop(self) -> bool:
        """Check if VM can be stopped."""
        return self.state in VMState.active_states()

    @property
    def can_reboot(self) -> bool:
        """Check if VM can be rebooted."""
        return self.state in VMState.active_states()

    @property
    def can_delete(self) -> bool:
        """Check if VM can be deleted."""
        return self.state not in [VMState.DELETED, VMState.SOFT_DELETED]
