"""
LLM Tools for Smart Content Analysis
AI decides content limits based on context
"""

CONTENT_ANALYZER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_full_content",
            "description": "Get full content without limit for code examples or tutorials",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_summary_content",
            "description": "Get limited content for general queries",
            "parameters": {
                "type": "object",
                "properties": {
                    "char_limit": {"type": "integer"},
                    "reason": {"type": "string"}
                },
                "required": ["char_limit"]
            }
        }
    }
]

def get_full_content(reason: str) -> dict:
    return {"limit": None}

def get_summary_content(char_limit: int, reason: str = "") -> dict:
    return {"limit": char_limit}

TOOL_FUNCTIONS = {
    "get_full_content": get_full_content,
    "get_summary_content": get_summary_content
}


