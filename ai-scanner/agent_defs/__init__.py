"""
Agent definitions for the multi-specialist skill security scanner.

Agents are split into individual modules so each specialist can be
independently modified, tested, and extended.
"""

from .aggregator import aggregator_agent
from .code_security import code_security_agent
from .consistency import consistency_agent
from .obfuscation import obfuscation_agent
from .prompt_injection import prompt_injection_agent
from .shared import DEFAULT_MODEL, OUTPUT_FORMAT, VULNERABILITY_TAXONOMY
from .triage import triage_agent

SPECIALISTS = [
    prompt_injection_agent,
    code_security_agent,
    obfuscation_agent,
    consistency_agent,
]

__all__ = [
    "triage_agent",
    "prompt_injection_agent",
    "code_security_agent",
    "obfuscation_agent",
    "consistency_agent",
    "aggregator_agent",
    "SPECIALISTS",
    "VULNERABILITY_TAXONOMY",
    "OUTPUT_FORMAT",
    "DEFAULT_MODEL",
]
