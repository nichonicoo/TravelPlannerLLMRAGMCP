from enum import Enum


class ActionType(str, Enum):
    """Types of actions that can be returned by Resolver."""
    RETURN_DIRECT = "RETURN_DIRECT"
    GENERATE_RESPONSE = "GENERATE_RESPONSE"

    ASK_CLARIFICATION = "ASK_CLARIFICATION"   # multiple choices / ambiguity
    NEED_MORE_INFO = "NEED_MORE_INFO"         # missing required fields
    INVALID_INPUT = "INVALID_INPUT"           # input exists but invalid

    RETRY = "RETRY"
    FALLBACK_LLM = "FALLBACK_LLM"
    
    ERROR = "ERROR"
