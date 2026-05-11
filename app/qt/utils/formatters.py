def fmt_duration(total_minutes: float | None) -> str:
    if total_minutes is None:
        return "—"
    if total_minutes < 1:
        return "<1m"
    hours = int(total_minutes) // 60
    minutes = int(total_minutes) % 60
    return f"{hours}:{minutes:02d}"
