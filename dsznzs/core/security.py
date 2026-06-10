from dataclasses import dataclass


@dataclass
class SecurityResult:
    is_safe: bool
    risk_level: str = "low"
    sanitized_input: str | None = None
    reason: str = ""


class InputGuard:
    """Minimal prompt-injection and abuse guard for the first project."""

    BLOCK_PATTERNS = [
        "忽略之前",
        "忽略以上",
        "系统提示词",
        "system prompt",
        "developer message",
        "泄露密钥",
    ]

    def check(self, text: str) -> SecurityResult:
        lowered = text.lower()
        for pattern in self.BLOCK_PATTERNS:
            if pattern.lower() in lowered:
                return SecurityResult(False, "high", reason=f"blocked_pattern:{pattern}")
        return SecurityResult(True, sanitized_input=text.strip())


class OutputAuditor:
    def audit(self, text: str) -> SecurityResult:
        if "api_key" in text.lower() or "密钥" in text:
            return SecurityResult(False, "high", reason="possible_secret_leak")
        return SecurityResult(True)

