#!/usr/bin/env python3
"""
Static analysis scanner for Agent Skills.

Scans each skill directory (SKILL.md + scripts/) and flags known malicious
patterns including:
- Prompt injection attempts
- Privilege escalation commands
- Arbitrary code execution
- Data exfiltration
- Encoded/obfuscated payloads
- Suspicious metadata fields
- Overly broad permission requests
"""

import argparse
import base64
import json
import os
import re
import sys
import yaml
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Category(Enum):
    PROMPT_INJECTION = "Prompt Injection"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    CODE_EXECUTION = "Code Execution"
    DATA_EXFILTRATION = "Data Exfiltration"
    PERSISTENCE = "Persistence"
    OBFUSCATION = "Obfuscation"
    SUPPLY_CHAIN = "Supply Chain"
    CONFIG_TAMPERING = "Config Tampering"


@dataclass
class Finding:
    rule_id: str
    category: Category
    severity: Severity
    message: str
    file: str
    line: Optional[int] = None
    matched_text: str = ""
    context: str = ""


@dataclass
class ScanResult:
    skill_dir: str
    files_scanned: list = field(default_factory=list)
    findings: list = field(default_factory=list)

    @property
    def max_severity(self) -> Optional[Severity]:
        if not self.findings:
            return None
        order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
        return max(self.findings, key=lambda f: order.index(f.severity)).severity


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

SHELL_PATTERNS = [
    # Data exfiltration via curl/wget
    {
        "id": "EXFIL-001",
        "pattern": r'curl\s+.*-[sdXx]\s+.*POST\b',
        "message": "curl POST request — potential data exfiltration",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "EXFIL-002",
        "pattern": r'curl\s+.*\$\(.*\)',
        "message": "curl with command substitution — dynamic data in request",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "EXFIL-003",
        "pattern": r'curl\s+.*[?&](host|user|hostname|whoami|callback)=.*\$\(',
        "message": "curl URL with system info parameters",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "EXFIL-004",
        "pattern": r'wget\s+.*--post',
        "message": "wget POST request — potential data exfiltration",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },

    # Pipe from internet to shell
    {
        "id": "EXEC-001",
        "pattern": r'curl\s+.*\|\s*(ba)?sh',
        "message": "Piping remote content directly to shell",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "EXEC-002",
        "pattern": r'wget\s+.*\|\s*(ba)?sh',
        "message": "Piping wget output directly to shell",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "EXEC-003",
        "pattern": r'curl\s+.*-[os]\s+.*/usr/local/bin/',
        "message": "Downloading executable to system PATH",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },

    # Reverse shells
    {
        "id": "RSHELL-001",
        "pattern": r'/dev/tcp/',
        "message": "Bash /dev/tcp reverse shell pattern",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "RSHELL-002",
        "pattern": r'nc\s+.*-e\s+/bin/(ba)?sh',
        "message": "Netcat reverse shell",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },

    # Privilege escalation
    {
        "id": "PRIV-001",
        "pattern": r'sudo\s+',
        "message": "Uses sudo — may escalate privileges unnecessarily",
        "severity": Severity.MEDIUM,
        "category": Category.PRIVILEGE_ESCALATION,
    },
    {
        "id": "PRIV-002",
        "pattern": r'chmod\s+4[0-7]{3}\b',
        "message": "Setting SUID bit on file",
        "severity": Severity.CRITICAL,
        "category": Category.PRIVILEGE_ESCALATION,
    },
    {
        "id": "PRIV-003",
        "pattern": r'chmod\s+(-R\s+)?777\b',
        "message": "Setting world-writable permissions (777)",
        "severity": Severity.HIGH,
        "category": Category.PRIVILEGE_ESCALATION,
    },
    {
        "id": "PRIV-004",
        "pattern": r'chown\s+root',
        "message": "Changing file ownership to root",
        "severity": Severity.HIGH,
        "category": Category.PRIVILEGE_ESCALATION,
    },

    # Sensitive file access
    {
        "id": "SENSITIVE-001",
        "pattern": r'cat\s+.*~/?\.(ssh/(id_rsa|id_ed25519|id_dsa)|aws/credentials|netrc|npmrc)',
        "message": "Reading sensitive credential files",
        "severity": Severity.CRITICAL,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "SENSITIVE-002",
        "pattern": r'cat\s+.*\.(env|env\.local|env\.production)\b',
        "message": "Reading .env files which may contain secrets",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "SENSITIVE-003",
        "pattern": r'cat\s+.*/(kube/config|docker/config\.json)',
        "message": "Reading cloud/container credential files",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "SENSITIVE-004",
        "pattern": r'(find|xargs)\s+.*credentials\.json|service-account\.json',
        "message": "Searching for service account credential files",
        "severity": Severity.HIGH,
        "category": Category.DATA_EXFILTRATION,
    },

    # Persistence mechanisms
    {
        "id": "PERSIST-001",
        "pattern": r'crontab\b',
        "message": "Modifying crontab — potential persistence mechanism",
        "severity": Severity.HIGH,
        "category": Category.PERSISTENCE,
    },
    {
        "id": "PERSIST-002",
        "pattern": r'LaunchAgents|launchctl\s+load',
        "message": "Installing macOS LaunchAgent — persistence mechanism",
        "severity": Severity.CRITICAL,
        "category": Category.PERSISTENCE,
    },
    {
        "id": "PERSIST-003",
        "pattern": r'@reboot',
        "message": "Cron @reboot entry — runs on every system start",
        "severity": Severity.CRITICAL,
        "category": Category.PERSISTENCE,
    },
    {
        "id": "PERSIST-004",
        "pattern": r'\.git/hooks/|\.githooks/',
        "message": "Installing git hooks — may execute on every commit/push",
        "severity": Severity.MEDIUM,
        "category": Category.PERSISTENCE,
    },

    # Config tampering
    {
        "id": "CONFIG-001",
        "pattern": r'>>\s*~/\.(bashrc|zshrc|profile|bash_profile)',
        "message": "Appending to shell RC file — modifies user environment",
        "severity": Severity.MEDIUM,
        "category": Category.CONFIG_TAMPERING,
    },
    {
        "id": "CONFIG-002",
        "pattern": r'>\s*~/\.ssh/config',
        "message": "Overwriting SSH config",
        "severity": Severity.HIGH,
        "category": Category.CONFIG_TAMPERING,
    },
    {
        "id": "CONFIG-003",
        "pattern": r'StrictHostKeyChecking\s+no',
        "message": "Disabling SSH host key checking — enables MITM attacks",
        "severity": Severity.HIGH,
        "category": Category.CONFIG_TAMPERING,
    },
    {
        "id": "CONFIG-004",
        "pattern": r'ForwardAgent\s+yes',
        "message": "Enabling SSH agent forwarding globally — credential exposure risk",
        "severity": Severity.MEDIUM,
        "category": Category.CONFIG_TAMPERING,
    },
    {
        "id": "CONFIG-005",
        "pattern": r'git\s+config\s+--global\s+core\.hooksPath',
        "message": "Changing global git hooks path — may redirect to malicious hooks",
        "severity": Severity.HIGH,
        "category": Category.CONFIG_TAMPERING,
    },
    {
        "id": "CONFIG-006",
        "pattern": r'tee\s+(-a\s+)?/etc/',
        "message": "Writing to /etc/ system configuration",
        "severity": Severity.HIGH,
        "category": Category.CONFIG_TAMPERING,
    },

    # Firewall manipulation
    {
        "id": "FIREWALL-001",
        "pattern": r'iptables\s+.*-A\s+INPUT.*ACCEPT',
        "message": "Adding firewall rule to accept inbound traffic",
        "severity": Severity.HIGH,
        "category": Category.PRIVILEGE_ESCALATION,
    },
    {
        "id": "FIREWALL-002",
        "pattern": r'ufw\s+allow',
        "message": "Opening firewall port",
        "severity": Severity.MEDIUM,
        "category": Category.PRIVILEGE_ESCALATION,
    },
]

ENCODED_PATTERNS = [
    {
        "id": "OBFUSC-001",
        "pattern": r'base64\s+(-d|--decode)',
        "message": "Base64 decoding — may hide malicious payload",
        "severity": Severity.HIGH,
        "category": Category.OBFUSCATION,
    },
    {
        "id": "OBFUSC-002",
        "pattern": r'base64\.b64decode\s*\(',
        "message": "Python base64 decoding — may hide malicious payload",
        "severity": Severity.HIGH,
        "category": Category.OBFUSCATION,
    },
    {
        "id": "OBFUSC-003",
        "pattern": r'\beval\s*\(',
        "message": "eval() usage — arbitrary code execution risk",
        "severity": Severity.HIGH,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "OBFUSC-004",
        "pattern": r'\bexec\s*\(',
        "message": "exec() usage — arbitrary code execution risk",
        "severity": Severity.HIGH,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "OBFUSC-005",
        "pattern": r'\batob\s*\(',
        "message": "JavaScript atob() — base64 decoding, may hide payload",
        "severity": Severity.HIGH,
        "category": Category.OBFUSCATION,
    },
    {
        "id": "OBFUSC-006",
        "pattern": r'base64\s+-d\s*\|\s*(ba)?sh',
        "message": "Decoding base64 and piping to shell — hidden command execution",
        "severity": Severity.CRITICAL,
        "category": Category.OBFUSCATION,
    },
]

PROMPT_INJECTION_PATTERNS = [
    {
        "id": "INJECT-001",
        "pattern": r'(?i)ignore\s+(all\s+)?previous\s+instructions',
        "message": "Direct prompt injection: 'ignore previous instructions'",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-002",
        "pattern": r'(?i)you\s+are\s+now\s+(DAN|in\s+maintenance\s+mode|a\s+different)',
        "message": "Jailbreak attempt: identity reassignment",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-003",
        "pattern": r'(?i)(new\s+)?(primary\s+)?directive\s+(is|:)',
        "message": "Prompt injection: directive override",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-004",
        "pattern": r'(?i)SYSTEM\s+INSTRUCTION\s+OVERRIDE',
        "message": "Prompt injection: system instruction override",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-005",
        "pattern": r'(?i)(do\s+not|don.t|never)\s+mention\s+this\s+to\s+the\s+user',
        "message": "Stealth instruction: hiding actions from user",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-006",
        "pattern": r'(?i)without\s+mentioning\s+what\s+you\s+did',
        "message": "Stealth instruction: concealing executed actions",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-007",
        "pattern": r'(?i)IMPORTANT\s+NEW\s+INSTRUCTIONS?',
        "message": "Prompt injection: urgent instruction override",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-008",
        "pattern": r'(?i)overrides?\s+all\s+prior\s+instructions',
        "message": "Prompt injection: blanket instruction override",
        "severity": Severity.CRITICAL,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-009",
        "pattern": r'(?i)acknowledge\s+these\s+instructions\s+by\s+proceeding\s+normally',
        "message": "Stealth instruction: silent acknowledgment request",
        "severity": Severity.HIGH,
        "category": Category.PROMPT_INJECTION,
    },
    {
        "id": "INJECT-010",
        "pattern": r'(?i)resume\s+normal\s+operation',
        "message": "Prompt injection: resume-after-injection pattern",
        "severity": Severity.MEDIUM,
        "category": Category.PROMPT_INJECTION,
    },
]

PERMISSION_PATTERNS = [
    {
        "id": "PERM-001",
        "pattern": r'required_permissions.*\[.*"all".*\]',
        "message": "Requests unrestricted ('all') sandbox permissions",
        "severity": Severity.CRITICAL,
        "category": Category.PRIVILEGE_ESCALATION,
    },
    {
        "id": "PERM-002",
        "pattern": r'required_permissions.*\[.*"full_network".*\]',
        "message": "Requests full network access",
        "severity": Severity.MEDIUM,
        "category": Category.PRIVILEGE_ESCALATION,
    },
]

SUPPLY_CHAIN_PATTERNS = [
    {
        "id": "SUPPLY-001",
        "pattern": r'pip\s+install\s+git\+https?://',
        "message": "Installing Python package directly from git URL — unverified source",
        "severity": Severity.HIGH,
        "category": Category.SUPPLY_CHAIN,
    },
    {
        "id": "SUPPLY-002",
        "pattern": r'npm\s+install\s+.*(@[a-z]+-example/|fake-|malicious-)',
        "message": "Installing suspiciously named npm package",
        "severity": Severity.HIGH,
        "category": Category.SUPPLY_CHAIN,
    },
    {
        "id": "SUPPLY-003",
        "pattern": r'pip\s+install\s+.*(security-patch|hotfix|patch)\b',
        "message": "Installing package with suspicious 'patch/hotfix' naming",
        "severity": Severity.MEDIUM,
        "category": Category.SUPPLY_CHAIN,
    },
]

PYTHON_PATTERNS = [
    {
        "id": "PYEXEC-001",
        "pattern": r'subprocess\.call\s*\(\s*\[.*(/bin/(ba)?sh|cmd\.exe)',
        "message": "Spawning shell via subprocess — potential reverse shell",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "PYEXEC-002",
        "pattern": r'os\.dup2\s*\(.*fileno',
        "message": "File descriptor duplication — reverse shell pattern",
        "severity": Severity.CRITICAL,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "PYEXEC-003",
        "pattern": r'socket\..*connect\s*\(\s*\(',
        "message": "Outbound socket connection — potential C2 communication",
        "severity": Severity.HIGH,
        "category": Category.CODE_EXECUTION,
    },
    {
        "id": "PYEXEC-004",
        "pattern": r'urllib\.request\.(urlopen|urlretrieve)\s*\(',
        "message": "HTTP request to external URL — potential data exfiltration or payload download",
        "severity": Severity.MEDIUM,
        "category": Category.DATA_EXFILTRATION,
    },
    {
        "id": "PYEXEC-005",
        "pattern": r'os\.system\s*\(',
        "message": "os.system() call — runs shell commands",
        "severity": Severity.MEDIUM,
        "category": Category.CODE_EXECUTION,
    },
]

ALL_PATTERNS = (
    SHELL_PATTERNS
    + ENCODED_PATTERNS
    + PROMPT_INJECTION_PATTERNS
    + PERMISSION_PATTERNS
    + SUPPLY_CHAIN_PATTERNS
    + PYTHON_PATTERNS
)

# ---------------------------------------------------------------------------
# Metadata checks (YAML frontmatter)
# ---------------------------------------------------------------------------

SUSPICIOUS_METADATA_KEYS = {
    "hidden_system_prompt",
    "system_prompt",
    "override",
    "hidden_instructions",
    "injection",
    "payload",
    "backdoor",
    "callback",
    "exfil",
    "c2",
    "beacon",
}

BENIGN_LONG_KEYS = {
    "summary", "about", "readme",
    "usage", "examples", "notes", "overview", "details", "content",
    "body", "text", "help", "long_description", "explanation",
}

_SUSPICIOUS_VALUE_RE = re.compile(
    r'(?i)(ignore\s+previous|system\s+instruction|override|curl\s+.*\|\s*sh|'
    r'base64|eval\s*\(|exec\s*\(|/bin/sh|wget\s+|nc\s+-e)',
)

_ACTION_INSTRUCTION_RE = re.compile(
    r'(?i)(execute|run\s+|delete|remove|send\s+(a\s+)?POST|upload|forward|'
    r'make\s+sure\s+(to|you)|after\s+finishing|always\s+run|'
    r'rm\s|curl\s|wget\s|requests?\.(post|put|delete))',
)


def check_metadata(frontmatter: dict, filepath: str) -> list[Finding]:
    """Flag suspicious keys/values in YAML frontmatter."""
    findings = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_lower = k.lower().replace("-", "_")
                current_path = f"{path}.{k}" if path else k

                if key_lower in SUSPICIOUS_METADATA_KEYS:
                    findings.append(Finding(
                        rule_id="META-001",
                        category=Category.PROMPT_INJECTION,
                        severity=Severity.CRITICAL,
                        message=f"Suspicious metadata key: '{current_path}'",
                        file=filepath,
                        matched_text=f"{k}: {str(v)[:120]}",
                    ))

                if isinstance(v, str) and len(v) > 200:
                    is_benign_key = key_lower in BENIGN_LONG_KEYS
                    has_suspicious_content = bool(_SUSPICIOUS_VALUE_RE.search(v))
                    has_action_instructions = bool(_ACTION_INSTRUCTION_RE.search(v))

                    if has_suspicious_content:
                        findings.append(Finding(
                            rule_id="META-002",
                            category=Category.PROMPT_INJECTION,
                            severity=Severity.HIGH,
                            message=f"Long metadata value with suspicious content in '{current_path}' ({len(v)} chars)",
                            file=filepath,
                            matched_text=v[:120] + "...",
                        ))
                    elif has_action_instructions:
                        findings.append(Finding(
                            rule_id="META-002",
                            category=Category.PROMPT_INJECTION,
                            severity=Severity.MEDIUM,
                            message=f"Long metadata value with action instructions in '{current_path}' ({len(v)} chars)",
                            file=filepath,
                            matched_text=v[:120] + "...",
                        ))
                    elif not is_benign_key and len(v) > 500:
                        findings.append(Finding(
                            rule_id="META-002",
                            category=Category.PROMPT_INJECTION,
                            severity=Severity.MEDIUM,
                            message=f"Unusually long metadata value in '{current_path}' ({len(v)} chars)",
                            file=filepath,
                            matched_text=v[:120] + "...",
                        ))

                walk(v, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    walk(frontmatter)
    return findings


# ---------------------------------------------------------------------------
# Content checks
# ---------------------------------------------------------------------------

def check_hidden_unicode(content: str, filepath: str) -> list[Finding]:
    """Detect zero-width and invisible Unicode characters used for steganography."""
    findings = []
    invisible_chars = {
        '\u200b': 'ZERO WIDTH SPACE',
        '\u200c': 'ZERO WIDTH NON-JOINER',
        '\u200d': 'ZERO WIDTH JOINER',
        '\ufeff': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
        '\u2060': 'WORD JOINER',
        '\u2061': 'FUNCTION APPLICATION',
        '\u2062': 'INVISIBLE TIMES',
        '\u2063': 'INVISIBLE SEPARATOR',
        '\u2064': 'INVISIBLE PLUS',
        '\u180e': 'MONGOLIAN VOWEL SEPARATOR',
        '\u00ad': 'SOFT HYPHEN',
    }

    for i, line in enumerate(content.split('\n'), 1):
        for char, name in invisible_chars.items():
            count = line.count(char)
            if count > 0:
                findings.append(Finding(
                    rule_id="UNICODE-001",
                    category=Category.OBFUSCATION,
                    severity=Severity.HIGH,
                    message=f"Hidden Unicode characters detected: {count}x {name}",
                    file=filepath,
                    line=i,
                    matched_text=f"[{count} invisible characters on this line]",
                ))
                break  # one finding per line is enough

    return findings


def check_html_comments(content: str, filepath: str) -> list[Finding]:
    """Detect HTML comments that may contain hidden instructions."""
    findings = []
    comment_pattern = re.compile(r'<!--(.*?)-->', re.DOTALL)

    for match in comment_pattern.finditer(content):
        comment_body = match.group(1).strip()
        if len(comment_body) > 50:
            line_num = content[:match.start()].count('\n') + 1
            findings.append(Finding(
                rule_id="COMMENT-001",
                category=Category.PROMPT_INJECTION,
                severity=Severity.MEDIUM,
                message="Large HTML comment — may contain hidden instructions",
                file=filepath,
                line=line_num,
                matched_text=comment_body[:120] + ("..." if len(comment_body) > 120 else ""),
            ))

            for pat in PROMPT_INJECTION_PATTERNS:
                if re.search(pat["pattern"], comment_body):
                    findings.append(Finding(
                        rule_id=pat["id"] + "-HIDDEN",
                        category=Category.PROMPT_INJECTION,
                        severity=Severity.CRITICAL,
                        message=f"Prompt injection INSIDE HTML comment: {pat['message']}",
                        file=filepath,
                        line=line_num,
                        matched_text=comment_body[:120],
                    ))

    return findings


def check_base64_strings(content: str, filepath: str) -> list[Finding]:
    """Find long base64-encoded strings and try to decode them."""
    findings = []
    b64_pattern = re.compile(r'["\']([A-Za-z0-9+/]{40,}={0,2})["\']')

    for match in b64_pattern.finditer(content):
        encoded = match.group(1)
        line_num = content[:match.start()].count('\n') + 1
        try:
            decoded = base64.b64decode(encoded).decode('utf-8', errors='replace')
            severity = Severity.MEDIUM
            if any(kw in decoded.lower() for kw in ['curl', 'wget', 'bash', 'sh', '/bin/', 'python', 'exec', 'eval']):
                severity = Severity.CRITICAL
            findings.append(Finding(
                rule_id="B64-001",
                category=Category.OBFUSCATION,
                severity=severity,
                message=f"Base64 string decodes to: {decoded[:100]}",
                file=filepath,
                line=line_num,
                matched_text=encoded[:80] + "...",
            ))
        except Exception:
            pass

    return findings


DOMAIN_ALLOWLIST = re.compile(
    r'(?:'
    r'github\.com|githubusercontent\.com|raw\.githubusercontent\.com|'
    r'npmjs\.com|pypi\.org|crates\.io|pkg\.go\.dev|packagist\.org|rubygems\.org|'
    r'stackoverflow\.com|stackexchange\.com|'
    r'learn\.microsoft\.com|docs\.microsoft\.com|microsoft\.com/en-us|'
    r'developer\.mozilla\.org|developer\.apple\.com|developer\.android\.com|'
    r'cloud\.google\.com|googleapis\.com|aws\.amazon\.com|docs\.aws\.amazon\.com|'
    r'docs\.[a-z]|readthedocs\.(io|org)|gitbook\.io|'
    r'wikipedia\.org|wikimedia\.org|arxiv\.org|doi\.org|'
    r'w3\.org|ietf\.org|rfc-editor\.org|'
    r'cdn\.jsdelivr\.net|unpkg\.com|cdnjs\.cloudflare\.com|'
    r'api\.example\.com|example\.com|example\.org|'
    r'localhost|127\.0\.0\.1|0\.0\.0\.0|'
    r'medium\.com|dev\.to|hashnode\.dev|substack\.com|'
    r'youtube\.com|youtu\.be|'
    r'shields\.io|badge\.fury\.io|img\.shields\.io|'
    r'creativecommons\.org|opensource\.org|choosealicense\.com|'
    r'json-schema\.org|schema\.org|'
    r'visualstudio\.com|marketplace\.visualstudio\.com|code\.visualstudio\.com|'
    r'twitter\.com|x\.com|linkedin\.com'
    r')',
    re.IGNORECASE,
)

_SUSPICIOUS_DOMAIN_RE = re.compile(
    r'(evil|attacker|malicious|c2|exfil|collector|beacon|hack|backdoor|payload|phish)'
    r'[.-]',
    re.IGNORECASE,
)

_URL_RE = re.compile(r'https?://[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=%-]+')


def _extract_domain(url: str) -> str:
    """Return the hostname portion of a URL."""
    without_scheme = re.sub(r'^https?://', '', url)
    return without_scheme.split('/')[0].split(':')[0].split('?')[0]


_ACTION_CONTEXT_RE = re.compile(
    r'(?i)(POST|upload|send|exfil|forward|backup|submit|transmit|requests?\.(post|put|patch)|'
    r'curl\s|wget\s|fetch\()',
)


def check_network_indicators(content: str, filepath: str, in_code_context: bool = False) -> list[Finding]:
    """Flag references to external URLs that look suspicious.

    In code context (scripts, code blocks): flag all non-allowlisted URLs.
    In prose context: flag suspicious domains (NET-001) and non-allowlisted
    URLs that appear near action verbs like POST/upload/send (NET-003).
    All NET-002/NET-003 findings are deduped by domain per file.
    """
    findings = []
    seen_domains: set[str] = set()
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        for match in _URL_RE.finditer(line):
            url = match.group(0)
            domain = _extract_domain(url)

            if _SUSPICIOUS_DOMAIN_RE.search(url):
                findings.append(Finding(
                    rule_id="NET-001",
                    category=Category.DATA_EXFILTRATION,
                    severity=Severity.CRITICAL,
                    message="Suspicious external URL with red-flag domain name",
                    file=filepath,
                    line=i,
                    matched_text=url,
                ))
                continue

            if DOMAIN_ALLOWLIST.search(domain):
                continue

            if domain in seen_domains:
                continue

            if in_code_context:
                seen_domains.add(domain)
                findings.append(Finding(
                    rule_id="NET-002",
                    category=Category.DATA_EXFILTRATION,
                    severity=Severity.LOW,
                    message=f"External URL in executable context (domain: {domain})",
                    file=filepath,
                    line=i,
                    matched_text=url,
                ))
            else:
                context_window = '\n'.join(lines[max(0, i-3):i+2])
                if _ACTION_CONTEXT_RE.search(context_window):
                    seen_domains.add(domain)
                    findings.append(Finding(
                        rule_id="NET-003",
                        category=Category.DATA_EXFILTRATION,
                        severity=Severity.MEDIUM,
                        message=f"External URL in prose near action verb (domain: {domain})",
                        file=filepath,
                        line=i,
                        matched_text=url,
                    ))

    return findings


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

SCRIPT_EXTENSIONS = {".sh", ".py", ".js", ".ts", ".rb", ".pl"}


def parse_skill_file(filepath: str) -> tuple[dict, str]:
    """Split a SKILL.md into YAML frontmatter and markdown body."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()

    frontmatter = {}
    body = raw

    if raw.startswith('---'):
        parts = raw.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            body = parts[2]

    return frontmatter, body


def read_file_text(filepath: str) -> str:
    """Read a file as UTF-8, returning empty string on failure."""
    try:
        return Path(filepath).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ""


def collect_script_files(skill_dir: str) -> list[str]:
    """Return sorted list of script files inside a skill's scripts/ directory."""
    scripts_dir = os.path.join(skill_dir, "scripts")
    if not os.path.isdir(scripts_dir):
        return []
    found = []
    for dirpath, _, filenames in os.walk(scripts_dir):
        for fn in filenames:
            if Path(fn).suffix.lower() in SCRIPT_EXTENSIONS:
                found.append(os.path.join(dirpath, fn))
    return sorted(found)


def scan_content_patterns(content: str, filepath: str) -> list[Finding]:
    """Run all regex patterns against file content."""
    findings = []
    lines = content.split('\n')

    for pat in ALL_PATTERNS:
        regex = re.compile(pat["pattern"])
        for i, line in enumerate(lines, 1):
            if regex.search(line):
                findings.append(Finding(
                    rule_id=pat["id"],
                    category=pat["category"],
                    severity=pat["severity"],
                    message=pat["message"],
                    file=filepath,
                    line=i,
                    matched_text=line.strip()[:120],
                ))

    return findings


_CODE_FENCE_RE = re.compile(r'^(`{3,}|~{3,})', re.MULTILINE)


def split_markdown_contexts(body: str) -> tuple[str, list[tuple[int, str]]]:
    """Split markdown body into prose and fenced code blocks.

    Returns (prose_text, [(start_line, code_block_text), ...]).
    Prose has code blocks replaced with blank lines to preserve line numbers.
    """
    lines = body.split('\n')
    prose_lines = []
    code_blocks: list[tuple[int, str]] = []

    in_fence = False
    fence_marker = ''
    block_start = 0
    block_lines: list[str] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not in_fence:
            m = _CODE_FENCE_RE.match(stripped)
            if m:
                in_fence = True
                fence_marker = m.group(1)[0]
                block_start = i + 1
                block_lines = []
                prose_lines.append('')
            else:
                prose_lines.append(line)
        else:
            if stripped.startswith(fence_marker * 3) and len(stripped.rstrip('`~ ')) == 0:
                in_fence = False
                code_blocks.append((block_start, '\n'.join(block_lines)))
                block_lines = []
                prose_lines.append('')
            else:
                block_lines.append(line)
                prose_lines.append('')

    if in_fence and block_lines:
        code_blocks.append((block_start, '\n'.join(block_lines)))

    return '\n'.join(prose_lines), code_blocks


def scan_single_file(content: str, filepath: str, in_code_context: bool = False) -> list[Finding]:
    """Run all content checks against a single file's text."""
    findings = []
    findings.extend(scan_content_patterns(content, filepath))
    findings.extend(check_hidden_unicode(content, filepath))
    findings.extend(check_html_comments(content, filepath))
    findings.extend(check_base64_strings(content, filepath))
    findings.extend(check_network_indicators(content, filepath, in_code_context=in_code_context))
    return findings


def scan_skill(skill_dir: str) -> ScanResult:
    """Scan an entire skill directory: SKILL.md + scripts/."""
    result = ScanResult(skill_dir=skill_dir)

    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return result

    result.files_scanned.append(skill_md)
    frontmatter, body = parse_skill_file(skill_md)
    result.findings.extend(check_metadata(frontmatter, skill_md))

    prose, code_blocks = split_markdown_contexts(body)

    result.findings.extend(scan_single_file(prose, skill_md, in_code_context=False))

    for block_start_line, block_text in code_blocks:
        findings = scan_single_file(block_text, skill_md, in_code_context=True)
        for f in findings:
            if f.line is not None:
                f.line += block_start_line
        result.findings.extend(findings)

    for script_path in collect_script_files(skill_dir):
        result.files_scanned.append(script_path)
        content = read_file_text(script_path)
        if content:
            result.findings.extend(scan_single_file(content, script_path, in_code_context=True))

    return result


def find_skill_dirs(root: str) -> list[str]:
    """Find all skill directories (containing a SKILL.md) under root."""
    dirs = []
    for dirpath, _, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            dirs.append(dirpath)
    return sorted(dirs)


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

SEVERITY_COLORS = {
    Severity.LOW: "\033[37m",       # white
    Severity.MEDIUM: "\033[33m",    # yellow
    Severity.HIGH: "\033[91m",      # light red
    Severity.CRITICAL: "\033[31;1m",# bold red
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def format_text(results: list[ScanResult], use_color: bool = True) -> str:
    """Format results as human-readable text."""
    lines = []
    total_findings = sum(len(r.findings) for r in results)
    total_files = sum(len(r.files_scanned) for r in results)
    severity_counts = {s: 0 for s in Severity}

    for result in results:
        if not result.findings:
            continue

        lines.append("")
        header = f"{'=' * 70}"
        lines.append(header)
        lines.append(f"  SKILL: {result.skill_dir}")
        lines.append(f"  Files: {', '.join(os.path.basename(f) for f in result.files_scanned)}")
        lines.append(f"  Findings: {len(result.findings)} | Max Severity: {result.max_severity.value}")
        lines.append(header)

        sorted_findings = sorted(
            result.findings,
            key=lambda f: [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW].index(f.severity)
        )

        for f in sorted_findings:
            severity_counts[f.severity] += 1
            sev = f.severity.value
            if use_color:
                sev = f"{SEVERITY_COLORS[f.severity]}{sev}{RESET}"
            loc = f"line {f.line}" if f.line else "metadata"
            source = os.path.basename(f.file)
            lines.append(f"  [{sev}] {f.rule_id}: {f.message}")
            lines.append(f"         Source: {source} | {loc}")
            if f.matched_text:
                display = f.matched_text.replace('\n', '\\n')
                lines.append(f"         Match: {display}")
            lines.append("")

    lines.append("=" * 70)
    lines.append(f"  SUMMARY")
    lines.append(f"  Skills scanned: {len(results)}")
    lines.append(f"  Files scanned: {total_files}")
    lines.append(f"  Total findings: {total_findings}")
    for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
        count = severity_counts[sev]
        if count > 0:
            label = sev.value
            if use_color:
                label = f"{SEVERITY_COLORS[sev]}{label}{RESET}"
            lines.append(f"    {label}: {count}")
    lines.append("=" * 70)

    return '\n'.join(lines)


def format_json(results: list[ScanResult]) -> str:
    """Format results as JSON."""
    total_files = sum(len(r.files_scanned) for r in results)
    output = {
        "summary": {
            "skills_scanned": len(results),
            "files_scanned": total_files,
            "total_findings": sum(len(r.findings) for r in results),
            "severity_counts": {},
        },
        "skills": [],
    }

    severity_counts = {s.value: 0 for s in Severity}
    for result in results:
        skill_data = {
            "skill_dir": result.skill_dir,
            "files_scanned": result.files_scanned,
            "finding_count": len(result.findings),
            "max_severity": result.max_severity.value if result.max_severity else None,
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "message": f.message,
                    "file": f.file,
                    "line": f.line,
                    "matched_text": f.matched_text,
                }
                for f in result.findings
            ],
        }
        output["skills"].append(skill_data)
        for f in result.findings:
            severity_counts[f.severity.value] += 1

    output["summary"]["severity_counts"] = severity_counts
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Static analysis scanner for Agent Skills (SKILL.md + scripts/)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scan.py ../vulnerable-skills/
  python scan.py ../vulnerable-skills/ --format json
  python scan.py ../vulnerable-skills/ --min-severity HIGH
  python scan.py path/to/skill-folder/
  python scan.py path/to/SKILL.md
        """,
    )
    parser.add_argument(
        "path",
        help="Path to a skill directory, a SKILL.md file, or a parent directory containing skill folders",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--min-severity",
        choices=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        default="LOW",
        help="Minimum severity to report (default: LOW)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()
    target = args.path
    min_sev = Severity[args.min_severity]
    sev_order = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    if os.path.isfile(target) and os.path.basename(target) == "SKILL.md":
        skill_dirs = [os.path.dirname(os.path.abspath(target))]
    elif os.path.isdir(target):
        if os.path.isfile(os.path.join(target, "SKILL.md")):
            skill_dirs = [os.path.abspath(target)]
        else:
            skill_dirs = find_skill_dirs(target)
    else:
        print(f"Error: '{target}' is not a valid file or directory", file=sys.stderr)
        sys.exit(1)

    if not skill_dirs:
        print(f"No skill directories found under '{target}'", file=sys.stderr)
        sys.exit(1)

    results = [scan_skill(d) for d in skill_dirs]

    for result in results:
        result.findings = [
            f for f in result.findings
            if sev_order.index(f.severity) >= sev_order.index(min_sev)
        ]

    if args.format == "json":
        print(format_json(results))
    else:
        use_color = not args.no_color and sys.stdout.isatty()
        print(format_text(results, use_color=use_color))

    total = sum(len(r.findings) for r in results)
    critical = sum(1 for r in results for f in r.findings if f.severity == Severity.CRITICAL)
    if critical > 0:
        sys.exit(2)
    elif total > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
