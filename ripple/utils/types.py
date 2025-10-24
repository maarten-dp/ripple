from __future__ import annotations

# Re-export RecordType from base_record to avoid circular imports
from ..network.protocol.base_record import RecordType

__all__ = ["RecordType"]
