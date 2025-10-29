"""
Authentication module for validating GIBSONAI_MEMORI_API_KEY
"""

import httpx
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
import asyncpg
from fastapi import Header, HTTPException, Request

# datetime not used in this module; keep import commented for future use if needed
# from datetime import datetime
import tldextract


class User(BaseModel):
    """User model from API response"""

    id: str
    email: str
    full_name: str


class Project(BaseModel):
    """Project model from API response"""

    name: str


class ApiKeyInfo(BaseModel):
    """API key info model from API response"""

    created_at: str
    last_used_at: Optional[str] = None


class ValidationResponse(BaseModel):
    """Successful validation response model"""

    valid: bool
    user: User
    project: Project
    api_key_info: ApiKeyInfo


class AuthError(Exception):
    """Custom exception for authentication errors"""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ApiKeyValidator:
    """Class to handle API key validation"""

    def __init__(self):
        self.validation_url = (
            "https://jufrooeskbcpbtlaxvws.supabase.co/functions/v1/validate-api-key"
        )
        self.timeout = 10.0  # 10 seconds timeout

    async def validate_api_key(self, api_key: str) -> ValidationResponse:
        """
        Validate API key by making a request to the GibsonAI validation endpoint

        Args:
            api_key: The API key to validate

        Returns:
            ValidationResponse: The validation response if successful

        Raises:
            AuthError: If validation fails or API key is invalid
        """
        if not api_key:
            raise AuthError("Missing API key", 401)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url=self.validation_url, headers=headers)

                # Handle different response status codes
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return ValidationResponse(**data)
                    except Exception as e:
                        raise AuthError(f"Invalid response format: {str(e)}", 500)

                elif response.status_code == 401:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", "Invalid API key")
                        raise AuthError(error_message, 401)
                    except Exception:
                        raise AuthError("Invalid API key", 401)

                elif response.status_code == 500:
                    try:
                        error_data = response.json()
                        error_message = error_data.get(
                            "message", "Internal server error"
                        )
                        raise AuthError(
                            f"Validation service error: {error_message}", 500
                        )
                    except Exception:
                        raise AuthError("Validation service error", 500)

                else:
                    raise AuthError(
                        f"Unexpected response status: {response.status_code}", 500
                    )

        except httpx.TimeoutException:
            raise AuthError("API key validation timeout", 500)
        except httpx.RequestError as e:
            raise AuthError(f"Network error during validation: {str(e)}", 500)
        except AuthError:
            # Re-raise AuthError as-is
            raise
        except Exception as e:
            raise AuthError(f"Unexpected error during validation: {str(e)}", 500)


# Global validator instance
validator = ApiKeyValidator()


async def validate_api_key(api_key: str) -> ValidationResponse:
    """
    Convenience function to validate API key

    Args:
        api_key: The API key to validate

    Returns:
        ValidationResponse: The validation response if successful

    Raises:
        AuthError: If validation fails
    """
    return await validator.validate_api_key(api_key)


async def verify_api_key(
    authorization: str = Header(..., alias="Authorization"),
) -> ValidationResponse:
    """
    FastAPI dependency to verify the Authorization header and validate the API key

    Delegates to validate_api_key() defined in this module.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check Bearer format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = authorization.replace("Bearer ", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        validation_response = await validate_api_key(api_key)
        return validation_response
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _get_db_connection_for_auth():
    """Create an asyncpg connection using environment variables (local helper to avoid circular imports)."""
    try:
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = int(os.getenv("POSTGRES_PORT", "5432"))
        db_user = os.getenv("POSTGRES_USER", "do_user")
        db_password = os.getenv("POSTGRES_PASSWORD", "do_user_password")
        db_name = os.getenv("POSTGRES_DB", "customer_support")

        return await asyncio.wait_for(
            asyncpg.connect(
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                database=db_name,
            ),
            timeout=30.0,
        )
    except Exception as e:
        print(f"ERROR: auth._get_db_connection_for_auth failed: {e}")
        return None


async def verify_api_key_and_get_domain(
    authorization: str = Header(..., alias="Authorization"),
) -> dict:
    """
    FastAPI dependency to verify the API key and get associated domain info.

    This function:
    1. Validates the Bearer token format
    2. Validates the API key with GibsonAI service
    3. Looks up the domain associated with this API key in registered_domains table
    4. Returns domain information including website_url

    Returns:
        dict: {
            "validation": ValidationResponse,
            "domain_id": str,
            "domain_name": str,
            "website_url": str,
            "api_key": str
        }

    Raises:
        HTTPException: If authentication fails or no domain found for API key
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check Bearer format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = authorization.replace("Bearer ", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Step 1: Validate API key with GibsonAI service
        validation_response = await validate_api_key(api_key)

        # Step 2: Look up domain associated with this API key
        conn = await _get_db_connection_for_auth()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")

        try:
            row = await conn.fetchrow(
                "SELECT id, domain_name, api_key FROM registered_domains WHERE api_key = $1",
                api_key,
            )

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail="No domain registered for this API key. Please register your domain first using /register-domain endpoint.",
                )

            # Construct website_url from domain_name
            domain_name = row["domain_name"]
            # Ensure it has https:// prefix
            if not domain_name.startswith(("http://", "https://")):
                website_url = f"https://{domain_name}"
            else:
                website_url = domain_name

            return {
                "validation": validation_response,
                "domain_id": str(row["id"]),
                "domain_name": domain_name,
                "website_url": website_url,
                "api_key": api_key,
            }
        finally:
            await conn.close()

    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_domain_id(
    request: Request,
    x_domain_id: Optional[str] = Header(None, alias="X-Domain-ID"),
):
    """
    FastAPI dependency to validate X-Domain-ID header against registered_domains table.

    Returns small dict with domain metadata on success. Raises HTTPException on failure.
    """
    if not x_domain_id:
        raise HTTPException(status_code=400, detail="Missing X-Domain-ID header")

    conn = await _get_db_connection_for_auth()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        row = await conn.fetchrow(
            "SELECT id, domain_name, api_key, created_at FROM registered_domains WHERE id = $1",
            x_domain_id,
        )
        if not row:
            raise HTTPException(status_code=401, detail="Unknown domain_id")

        # More robust normalization and matching for stored domain values.
        # Extract two identifiers from the stored domain_name:
        #  - registered_reg: the tldextract registered domain (e.g., 'lovable.app')
        #  - registered_host: the host with leading 'www.' removed (e.g., 'preview--chat-tally.lovable.app')
        def extract_registered_identifiers(value: Optional[str]):
            if not value:
                return None, None
            try:
                from urllib.parse import urlparse

                parsed = urlparse(value)
                host = parsed.hostname if parsed.hostname else value
            except Exception:
                host = value

            host = host.lower().strip() if host else None
            host_no_www = host[4:] if host and host.startswith("www.") else host

            try:
                ext = tldextract.extract(host or "")
                registered = (
                    ext.registered_domain.lower()
                    if ext and ext.registered_domain
                    else None
                )
            except Exception:
                registered = None

            return registered, host_no_www

        registered_reg, registered_host = extract_registered_identifiers(
            row["domain_name"]
        )
        # Fallback to raw stored value lowercased if no host part extracted
        if not registered_host:
            registered_host = (
                row["domain_name"].lower() if row.get("domain_name") else None
            )

        origin = request.headers.get("origin") or request.headers.get("Origin")
        referer = request.headers.get("referer") or request.headers.get("Referer")

        def extract_host_from_url(url: Optional[str]) -> Optional[str]:
            if not url:
                return None
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                return (parsed.hostname or url).lower()
            except Exception:
                return url.lower()

        origin_host = extract_host_from_url(origin)
        referer_host = extract_host_from_url(referer)

        debug = os.getenv("DEBUG_DOMAIN_MATCHING", "0") == "1"

        def host_matches_registered(
            host: Optional[str],
            registered_reg: Optional[str],
            registered_host_val: Optional[str],
        ) -> bool:
            """
            Matches if any of the following is true:
             - host equals stored host (without www)
             - host is a subdomain of stored host
             - tldextract.registered_domain(host) equals stored registered_reg
            """
            if not host:
                return False
            host = host.lower().strip()
            host_no_www = host[4:] if host.startswith("www.") else host

            # Exact match against stored host
            if registered_host_val and (
                host == registered_host_val or host_no_www == registered_host_val
            ):
                return True

            # Subdomain match
            if registered_host_val and (
                host.endswith("." + registered_host_val)
                or host_no_www.endswith("." + registered_host_val)
            ):
                return True

            # Compare tldextract registered domains if available
            if registered_reg:
                try:
                    ext = tldextract.extract(host)
                    host_registered = (
                        ext.registered_domain.lower() if ext.registered_domain else None
                    )
                    if host_registered and host_registered == registered_reg:
                        return True
                except Exception:
                    pass

            return False

        if origin_host or referer_host:
            ok = host_matches_registered(
                origin_host, registered_reg, registered_host
            ) or host_matches_registered(referer_host, registered_reg, registered_host)
            if not ok:
                if debug:
                    print(
                        "DEBUG: domain match failed:\n",
                        "stored domain_name=",
                        row.get("domain_name"),
                        "registered_reg=",
                        registered_reg,
                        "registered_host=",
                        registered_host,
                        "origin=",
                        origin,
                        "origin_host=",
                        origin_host,
                        "referer=",
                        referer,
                        "referer_host=",
                        referer_host,
                    )
                raise HTTPException(
                    status_code=403,
                    detail="Request origin does not match registered domain",
                )

        # Return the original stored domain_name alongside the id and api_key.
        return {
            "id": row["id"],
            "domain_name": row["domain_name"],
            "api_key": row["api_key"],
        }
    finally:
        await conn.close()
