"""Context prompts per condition. Built from frozen job records only, never from the utterance's readings."""

from fvr.synth import GENERIC_TERMS, Equipment, Job, Utterance, job_record_terms

CONDITIONS = ["none", "generic", "job", "stale", "wrong", "oracle"]


def _record_prompt(trade: str, complaint: str, equipment: list[Equipment], terms: list[str]) -> str:
    gear = "; ".join(f"{e.brand} {e.type}, model {e.model}" for e in equipment)
    return f"{trade.upper()} service call, {complaint}. Equipment on site: {gear}. Parts and terms: {', '.join(terms)}."


def wrong_job(job: Job, jobs: list[Job]) -> Job:
    """A fixed other customer's job with a different trade (the wrong record was opened)."""
    i = jobs.index(job)
    for k in range(1, len(jobs)):
        other = jobs[(i + len(jobs) // 2 + k) % len(jobs)]
        if other.trade != job.trade:
            return other
    raise ValueError("no job with a different trade")


def prompt_for(condition: str, utt: Utterance, job: Job, jobs: list[Job]) -> str | None:
    if condition == "none":
        return None
    if condition == "generic":
        return "Home service call: HVAC, plumbing or electrical. Terms: " + ", ".join(GENERIC_TERMS) + "."
    if condition == "job":
        return _record_prompt(job.trade, job.complaint, job.equipment, job_record_terms(job))
    if condition == "stale":
        return _record_prompt(job.trade, job.complaint, job.stale_equipment, job_record_terms(job))
    if condition == "wrong":
        other = wrong_job(job, jobs)
        return _record_prompt(other.trade, other.complaint, other.equipment, job_record_terms(other))
    if condition == "oracle":
        targets = utt.ids + utt.terms
        return ("Terms: " + ", ".join(targets) + ".") if targets else None
    raise ValueError(condition)
