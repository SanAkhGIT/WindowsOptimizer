def verify_tweak(tweak):
    if not tweak.check:
        return None, "No verification method defined."
    try:
        state=bool(tweak.check())
        return state, "Verified current state." if state else "Operation completed but expected state was not detected."
    except Exception as exc:
        return False, f"Verification failed: {exc}"
