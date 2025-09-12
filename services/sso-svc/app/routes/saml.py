"""
SAML authentication endpoints and handlers.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import RedirectResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_session
from ..models import IdentityProvider, UserSession, AuditLog
from ..config import get_settings
from ..services.saml_handler import SAMLHandler
from ..services.session_manager import SessionManager

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/metadata")
async def get_saml_metadata(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """
    Generate SAML Service Provider metadata.

    Returns XML metadata describing this service provider's
    capabilities and endpoints for identity providers.
    """
    try:
        saml_handler = SAMLHandler()
        metadata_xml = saml_handler.generate_sp_metadata(
            base_url=str(request.base_url).rstrip("/")
        )

        return PlainTextResponse(
            content=metadata_xml,
            media_type="application/xml",
            headers={
                "Content-Disposition": "attachment; filename=\"saml-metadata.xml\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate SAML metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SAML metadata")


@router.get("/login/{provider_id}")
async def initiate_saml_login(
    provider_id: str,
    request: Request,
    relay_state: str = None,
    force_authn: bool = False,
    session: AsyncSession = Depends(get_session)
):
    """
    Initiate SAML authentication with an identity provider.

    Creates SAML authentication request and redirects user to
    the identity provider's SSO endpoint.
    """
    try:
        # Get identity provider
        result = await session.execute(
            select(IdentityProvider).where(IdentityProvider.id == provider_id)
        )
        provider = result.scalar_one_or_none()

        if not provider or not provider.is_active():
            raise HTTPException(status_code=404, detail="Identity provider not found or inactive")

        # Initialize SAML handler
        saml_handler = SAMLHandler(provider)

        # Generate SAML authentication request
        auth_request_data = saml_handler.create_authn_request(
            base_url=str(request.base_url).rstrip("/"),
            relay_state=relay_state,
            force_authn=force_authn
        )

        # Create audit log
        audit_log = AuditLog(
            event_type="saml_auth_initiated",
            actor_type="user",
            action="initiate_login",
            description=f"SAML authentication initiated with provider {provider.name}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            provider_id=provider.id,
            provider_name=provider.name,
            success=True,
            tenant_id=provider.tenant_id,
            metadata={
                "relay_state": relay_state,
                "force_authn": force_authn,
                "request_id": auth_request_data.get("request_id")
            }
        )
        session.add(audit_log)
        await session.commit()

        # Redirect to identity provider
        if auth_request_data.get("method") == "POST":
            # Return HTML form for POST binding
            form_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Redirecting to Identity Provider</title>
            </head>
            <body onload="document.forms[0].submit()">
                <form method="post" action="{auth_request_data['sso_url']}">
                    <input type="hidden" name="SAMLRequest" value="{auth_request_data['saml_request']}" />
                    {f'<input type="hidden" name="RelayState" value="{relay_state}" />' if relay_state else ''}
                    <noscript>
                        <p>Please click the button below to continue to the identity provider:</p>
                        <input type="submit" value="Continue" />
                    </noscript>
                </form>
                <p>Redirecting to identity provider...</p>
            </body>
            </html>
            """
            return Response(content=form_html, media_type="text/html")
        else:
            # HTTP Redirect binding
            redirect_url = auth_request_data["redirect_url"]
            return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate SAML login: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate SAML authentication")


@router.post("/acs")
async def saml_assertion_consumer_service(
    request: Request,
    SAMLResponse: str = Form(...),
    RelayState: str = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """
    SAML Assertion Consumer Service (ACS) endpoint.

    Processes SAML responses from identity providers and
    creates user sessions upon successful authentication.
    """
    try:
        # Decode and validate SAML response
        saml_handler = SAMLHandler()
        validation_result = await saml_handler.process_saml_response(
            saml_response=SAMLResponse,
            session=session
        )

        if not validation_result["valid"]:
            # Create audit log for failed authentication
            audit_log = AuditLog.create_login_event(
                success=False,
                email=validation_result.get("email"),
                provider_id=validation_result.get("provider_id"),
                provider_name=validation_result.get("provider_name"),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                error_message=validation_result.get("error"),
                tenant_id=validation_result.get("tenant_id")
            )
            session.add(audit_log)
            await session.commit()

            raise HTTPException(
                status_code=400,
                detail=f"SAML authentication failed: {validation_result.get('error')}"
            )

        # Create user session
        session_manager = SessionManager(session)
        user_session = await session_manager.create_session(
            user_id=validation_result["user_id"],
            email=validation_result["email"],
            provider_id=validation_result["provider_id"],
            user_attributes=validation_result["attributes"],
            roles=validation_result["roles"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            tenant_id=validation_result["tenant_id"]
        )

        # Create audit log for successful authentication
        audit_log = AuditLog.create_login_event(
            success=True,
            user_id=validation_result["user_id"],
            email=validation_result["email"],
            provider_id=validation_result["provider_id"],
            provider_name=validation_result["provider_name"],
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            tenant_id=validation_result["tenant_id"],
            session_id=str(user_session.id)
        )
        session.add(audit_log)
        await session.commit()

        # Determine redirect URL
        if RelayState:
            redirect_url = RelayState
        else:
            # Default redirect URL (could be configured per tenant)
            redirect_url = "/dashboard"

        # Set session cookie and redirect
        response = RedirectResponse(url=redirect_url, status_code=302)
        response.set_cookie(
            key="sso_session",
            value=user_session.session_token,
            max_age=user_session.get_time_until_expiry().total_seconds(),
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process SAML response: {e}")

        # Create audit log for error
        audit_log = AuditLog.create_security_event(
            event_type="invalid_saml_response",
            description=f"Failed to process SAML response: {str(e)}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            error_message=str(e)
        )
        session.add(audit_log)
        await session.commit()

        raise HTTPException(status_code=500, detail="Failed to process SAML authentication")


@router.get("/sls")
@router.post("/sls")
async def saml_single_logout_service(
    request: Request,
    SAMLRequest: str = None,
    SAMLResponse: str = None,
    RelayState: str = None,
    SigAlg: str = None,
    Signature: str = None,
    session: AsyncSession = Depends(get_session)
):
    """
    SAML Single Logout Service (SLS) endpoint.

    Handles both logout requests from identity providers and
    logout responses to our logout requests.
    """
    try:
        saml_handler = SAMLHandler()

        if SAMLRequest:
            # Process logout request from IdP
            logout_data = await saml_handler.process_logout_request(
                saml_request=SAMLRequest,
                signature=Signature,
                sig_alg=SigAlg,
                session=session
            )

            if logout_data["valid"]:
                # Terminate user session
                session_manager = SessionManager(session)
                await session_manager.terminate_session_by_saml_id(
                    saml_session_id=logout_data["session_id"],
                    reason="saml_logout"
                )

                # Generate logout response
                logout_response = saml_handler.create_logout_response(
                    request_id=logout_data["request_id"],
                    status="success"
                )

                # Create audit log
                audit_log = AuditLog(
                    event_type="logout",
                    actor_type="user",
                    actor_id=logout_data.get("user_id"),
                    action="saml_logout",
                    description="User logged out via SAML SLO",
                    ip_address=request.client.host,
                    success=True,
                    tenant_id=logout_data.get("tenant_id")
                )
                session.add(audit_log)
                await session.commit()

                # Return logout response
                if logout_response.get("method") == "POST":
                    form_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head><title>Logout Response</title></head>
                    <body onload="document.forms[0].submit()">
                        <form method="post" action="{logout_response['slo_url']}">
                            <input type="hidden" name="SAMLResponse" value="{logout_response['saml_response']}" />
                            {f'<input type="hidden" name="RelayState" value="{RelayState}" />' if RelayState else ''}
                        </form>
                    </body>
                    </html>
                    """
                    return Response(content=form_html, media_type="text/html")
                else:
                    return RedirectResponse(url=logout_response["redirect_url"])
            else:
                raise HTTPException(status_code=400, detail="Invalid logout request")

        elif SAMLResponse:
            # Process logout response from IdP
            logout_result = await saml_handler.process_logout_response(
                saml_response=SAMLResponse,
                session=session
            )

            if logout_result["valid"]:
                # Redirect to logout completion page
                redirect_url = RelayState or "/logout/complete"
                return RedirectResponse(url=redirect_url)
            else:
                raise HTTPException(status_code=400, detail="Invalid logout response")
        else:
            raise HTTPException(status_code=400, detail="Missing SAML request or response")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process SAML logout: {e}")
        raise HTTPException(status_code=500, detail="Failed to process SAML logout")


@router.post("/logout/{session_token}")
async def initiate_logout(
    session_token: str,
    request: Request,
    relay_state: str = None,
    db_session: AsyncSession = Depends(get_session)
):
    """
    Initiate SAML logout for a user session.

    Creates SAML logout request and redirects to identity provider
    for single logout.
    """
    try:
        # Get user session
        session_manager = SessionManager(db_session)
        user_session = await session_manager.get_session_by_token(session_token)

        if not user_session or not user_session.is_active():
            raise HTTPException(status_code=404, detail="Session not found or expired")

        # Get identity provider
        result = await db_session.execute(
            select(IdentityProvider).where(IdentityProvider.id == user_session.provider_id)
        )
        provider = result.scalar_one_or_none()

        if not provider:
            # Local logout only
            await session_manager.terminate_session(user_session.id, "logout")
            return {"message": "Logged out successfully"}

        # Create SAML logout request
        saml_handler = SAMLHandler(provider)
        logout_request = saml_handler.create_logout_request(
            name_id=user_session.user_id,
            session_index=user_session.saml_session_id,
            relay_state=relay_state
        )

        # Terminate local session
        await session_manager.terminate_session(user_session.id, "logout_initiated")

        # Create audit log
        audit_log = AuditLog(
            event_type="logout",
            actor_type="user",
            actor_id=user_session.user_id,
            action="initiate_logout",
            description="SAML logout initiated",
            ip_address=request.client.host,
            success=True,
            tenant_id=user_session.tenant_id
        )
        db_session.add(audit_log)
        await db_session.commit()

        # Redirect to identity provider
        if logout_request.get("method") == "POST":
            form_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Logout Request</title></head>
            <body onload="document.forms[0].submit()">
                <form method="post" action="{logout_request['slo_url']}">
                    <input type="hidden" name="SAMLRequest" value="{logout_request['saml_request']}" />
                    {f'<input type="hidden" name="RelayState" value="{relay_state}" />' if relay_state else ''}
                </form>
            </body>
            </html>
            """
            return Response(content=form_html, media_type="text/html")
        else:
            return RedirectResponse(url=logout_request["redirect_url"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate logout: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate logout")
