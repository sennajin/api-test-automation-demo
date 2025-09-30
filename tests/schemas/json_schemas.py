"""JSON Schema definitions for reqres.in API responses."""

from __future__ import annotations

USER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "description": "Unique user identifier"
        },
        "email": {
            "type": "string", 
            "format": "email",
            "minLength": 1,
            "description": "User's email address"
        },
        "first_name": {
            "type": "string",
            "minLength": 1,
            "description": "User's first name"
        },
        "last_name": {
            "type": "string",
            "minLength": 1,
            "description": "User's last name"
        },
        "avatar": {
            "type": "string", 
            "format": "uri",
            "minLength": 1,
            "description": "URL to user's avatar image"
        },
    },
    "required": ["id", "email", "first_name", "last_name", "avatar"],
    "additionalProperties": False,
}

SUPPORT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "url": {
            "type": "string", 
            "format": "uri",
            "minLength": 1,
            "description": "Support URL"
        },
        "text": {
            "type": "string",
            "minLength": 1,
            "description": "Support text message"
        },
    },
    "required": ["url", "text"],
    "additionalProperties": False,
}

# Base pagination schema for reuse
BASE_PAGINATION_SCHEMA = {
    "page": {
        "type": "integer", 
        "minimum": 1,
        "description": "Current page number"
    },
    "per_page": {
        "type": "integer", 
        "minimum": 1,
        "maximum": 100,
        "description": "Number of items per page"
    },
    "total": {
        "type": "integer", 
        "minimum": 0,
        "description": "Total number of items"
    },
    "total_pages": {
        "type": "integer", 
        "minimum": 1,
        "description": "Total number of pages"
    },
    "support": SUPPORT_SCHEMA,
}

LIST_USERS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **BASE_PAGINATION_SCHEMA,
        "data": {"type": "array", "items": USER_SCHEMA},
    },
    "required": ["page", "per_page", "total", "total_pages", "data", "support"],
    "additionalProperties": False,
}

SINGLE_USER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "data": USER_SCHEMA,
        "support": SUPPORT_SCHEMA,
    },
    "required": ["data", "support"],
    "additionalProperties": False,
}

CREATE_USER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "User's name"
        },
        "job": {
            "type": "string",
            "minLength": 1,
            "description": "User's job title"
        },
        "id": {
            "type": "string",
            "minLength": 1,
            "description": "Generated user ID"
        },
        "createdAt": {
            "type": "string", 
            "format": "date-time",
            "description": "Creation timestamp"
        },
        "age": {
            "type": "integer",
            "minimum": 0,
            "maximum": 150,
            "description": "User's age (optional)"
        },
        "email": {
            "type": "string", 
            "format": "email",
            "description": "User's email (optional)"
        },
    },
    "required": ["id", "createdAt"],
    "additionalProperties": True,
}

UPDATE_USER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Updated user's name"
        },
        "job": {
            "type": "string",
            "minLength": 1,
            "description": "Updated user's job title"
        },
        "updatedAt": {
            "type": "string", 
            "format": "date-time",
            "description": "Last update timestamp"
        },
    },
    "required": ["updatedAt"],
    "additionalProperties": False,
}

# Base schemas for reuse
BASE_ERROR_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "error": {
            "type": "string",
            "minLength": 1,
            "description": "Error message"
        },
    },
    "required": ["error"],
    "additionalProperties": False,
}

# Reuse base error schema
ERROR_SCHEMA = BASE_ERROR_SCHEMA

RESOURCE_LIST_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        **{k: v for k, v in BASE_PAGINATION_SCHEMA.items() if k != "total_pages"},
        "total_pages": {"type": "integer", "minimum": 0},  # Different minimum for resources
        "data": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "year": {"type": "integer"},
                    "color": {"type": "string"},
                    "pantone_value": {"type": "string"},
                },
                "required": ["id", "name", "year", "color", "pantone_value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["page", "per_page", "total", "total_pages", "data", "support"],
    "additionalProperties": False,
}

LOGIN_SUCCESS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "token": {
            "type": "string",
            "minLength": 1,
            "description": "Authentication token"
        },
    },
    "required": ["token"],
    "additionalProperties": False,
}

# Register success schema (includes id field)
REGISTER_SUCCESS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "minimum": 1,
            "description": "User ID"
        },
        "token": {
            "type": "string",
            "minLength": 1,
            "description": "Authentication token"
        },
    },
    "required": ["id", "token"],
    "additionalProperties": False,
}

# Reuse base error schema instead of duplicating
LOGIN_ERROR_SCHEMA = BASE_ERROR_SCHEMA

# Additional comprehensive schemas for better validation
VALIDATION_ERROR_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "error": {
            "type": "string",
            "minLength": 1,
            "description": "Validation error message"
        },
        "field": {
            "type": "string",
            "description": "Field that failed validation"
        },
        "code": {
            "type": "string",
            "description": "Error code"
        }
    },
    "required": ["error"],
    "additionalProperties": True,
}

# Schema for empty responses (like 404)
EMPTY_RESPONSE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

# Schema for successful deletion responses (204 with empty body)
DELETE_SUCCESS_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "null",
    "description": "Empty response body for successful deletion"
}