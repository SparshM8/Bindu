"""Environment variable validation utilities for Bindu examples.

This module provides helper functions to validate required environment variables
and provide clear error messages when they are missing.
"""

import os
import sys
from typing import Optional

def get_required_env(
    var_name: str,
    error_message: Optional[str] = None
) -> str:
    """Get a required environment variable or exit with a helpful message.

    Args:
        var_name: Name of the environment variable
        error_message: Optional custom error message

    Returns:
        The environment variable value

    Raises:
        SystemExit: If the environment variable is not set
    """
    value = os.getenv(var_name)
    
    if not value:
        if error_message:
            print(f"\n❌ Error: {error_message}\n", file=sys.stderr)
        else:
            print(f"\n❌ Error: Required environment variable '{var_name}' is not set.\n", file=sys.stderr)
            print(f"Please set it in your .env file or export it:", file=sys.stderr)
            print(f"  export {var_name}='your-value-here'\n", file=sys.stderr)
            
            # Provide specific guidance for common API keys
            if var_name == "OPENROUTER_API_KEY":
                print("To get an OpenRouter API key:", file=sys.stderr)
                print("  1. Visit https://openrouter.ai/", file=sys.stderr)
                print("  2. Sign up for a free account", file=sys.stderr)
                print("  3. Go to Settings > API Keys", file=sys.stderr)
                print("  4. Create a new API key", file=sys.stderr)
                print("  5. Add it to your .env file: OPENROUTER_API_KEY=your-key-here\n", file=sys.stderr)
            elif var_name == "OPENAI_API_KEY":
                print("To get an OpenAI API key:", file=sys.stderr)
                print("  1. Visit https://platform.openai.com/", file=sys.stderr)
                print("  2. Sign up or log in", file=sys.stderr)
                print("  3. Go to API Keys section", file=sys.stderr)
                print("  4. Create a new API key", file=sys.stderr)
                print("  5. Add it to your .env file: OPENAI_API_KEY=your-key-here\n", file=sys.stderr)
        
        sys.exit(1)
    
    return value


def get_optional_env(
    var_name: str,
    default: str = "",
    warning_message: Optional[str] = None
) -> str:
    """Get an optional environment variable with a default value.

    Args:
        var_name: Name of the environment variable
        default: Default value if not set
        warning_message: Optional warning message to display if not set

    Returns:
        The environment variable value or default
    """
    value = os.getenv(var_name)
    
    if not value:
        if warning_message:
            print(f"\n⚠️  Warning: {warning_message}\n", file=sys.stderr)
        return default
    
    return value


def validate_api_keys(*required_keys: str) -> dict[str, str]:
    """Validate multiple required API keys at once.

    Args:
        *required_keys: Variable names of required API keys

    Returns:
        Dictionary mapping variable names to their values

    Raises:
        SystemExit: If any required key is missing
    """
    keys = {}
    missing_keys = []
    
    for key_name in required_keys:
        value = os.getenv(key_name)
        if value:
            keys[key_name] = value
        else:
            missing_keys.append(key_name)
    
    if missing_keys:
        print(f"\n❌ Error: Missing required API key(s): {', '.join(missing_keys)}\n", file=sys.stderr)
        print("Please set them in your .env file or export them:\n", file=sys.stderr)
        for key in missing_keys:
            print(f"  export {key}='your-value-here'", file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)
    
    return keys
