"""Executable symbolic oracle for the cabinet pilot.

It establishes obligations for a generated prompt; it does not grade free
text automatically or decide which new events a model has written.
"""

from __future__ import annotations

from dataclasses import dataclass


def minutes(clock: str) -> int:
    hour, minute = map(int, clock.split(":"))
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"Invalid time: {clock}")
    return 60 * hour + minute


def clock_time(value: int) -> str:
    if not 0 <= value < 24 * 60:
        raise ValueError("Time outside one day")
    return f"{value // 60}:{value % 60:02d}"


@dataclass(frozen=True)
class CabinetState:
    holder: str
    opened_at_0900: bool
    action_at_0900: str
    power_time: str


def execute_cabinet(
    transfers: list[str], power_time: str, *, decision_time: str = "9:00"
) -> CabinetState:
    if len(transfers) < 2 or len(transfers) != len(set(transfers)):
        raise ValueError("A transfer chain needs distinct holders")
    opened = minutes(power_time) <= minutes(decision_time)
    return CabinetState(transfers[-1], opened, "open" if opened else "wait", power_time)


def delayed_power(time: str, delay_minutes: int = 10) -> str:
    return clock_time(minutes(time) + delay_minutes)
