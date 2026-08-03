"""Decode operation sequences into feasible schedules and makespan."""

from __future__ import annotations

from dataclasses import dataclass

from optimize.domains.scheduling.jsp.loader import JSPInstance


@dataclass(frozen=True)
class ScheduledOperation:
    job: int
    operation_index: int
    machine: int
    processing_time: int
    start: int
    finish: int


@dataclass(frozen=True)
class Schedule:
    makespan: int
    operations: tuple[ScheduledOperation, ...]


def build_operation_labels(num_jobs: int, num_machines: int) -> list[int]:
    """Fixed labels: each job appears exactly num_machines times."""
    labels: list[int] = []
    for job in range(num_jobs):
        labels.extend([job] * num_machines)
    return labels


def decode_schedule(instance: JSPInstance, operation_sequence: list[int]) -> Schedule:
    """Serial schedule generation from an operation-based job sequence."""
    num_jobs = instance.num_jobs
    num_machines = instance.num_machines
    next_operation = [0] * num_jobs
    job_ready = [0] * num_jobs
    machine_ready = [0] * instance.num_machines
    scheduled: list[ScheduledOperation] = []

    for job in operation_sequence:
        op_index = next_operation[job]
        if op_index >= num_machines:
            raise ValueError(f"operation sequence schedules too many operations for job {job}")

        machine = instance.machines[job][op_index]
        duration = instance.processing_times[job][op_index]
        start = max(job_ready[job], machine_ready[machine])
        finish = start + duration

        scheduled.append(
            ScheduledOperation(
                job=job,
                operation_index=op_index,
                machine=machine,
                processing_time=duration,
                start=start,
                finish=finish,
            ),
        )

        next_operation[job] += 1
        job_ready[job] = finish
        machine_ready[machine] = finish

    if any(count != num_machines for count in next_operation):
        raise ValueError("operation sequence does not include every job operation exactly once")

    makespan = max(operation.finish for operation in scheduled)
    return Schedule(makespan=makespan, operations=tuple(scheduled))


def compute_makespan(instance: JSPInstance, operation_sequence: list[int]) -> int:
    return decode_schedule(instance, operation_sequence).makespan
