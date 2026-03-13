import json
import logging
import io

import qrcode
import requests

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class NDILoginController(http.Controller):

    def _get_ndi_config(self):
        """
        Read Bhutan NDI configuration from Odoo system parameters.
        """
        icp = request.env["ir.config_parameter"].sudo()
        return {
            "base_url": icp.get_param(
                "ndi.base_url",
                "https://demo-client.bhutanndi.com",
            ),
            "access_token": icp.get_param("ndi.access_token", ""),
            "webhook_id": icp.get_param("ndi.webhook_id", ""),
            "schema_name": icp.get_param(
                "ndi.schema_name",
                "https://dev-schema.ngotag.com/schemas/c7952a0a-e9b5-4a4b-a714-1e5d0a1ae076",
            ),
            "schema_mobile_number": icp.get_param(
                "ndi.schema_mobile_number",
                "https://dev-schema.ngotag.com/schemas/a2dcb671-3d64-47ec-ba59-97a3e642c724",
            ),
            "schema_email": icp.get_param(
                "ndi.schema_email",
                "https://dev-schema.ngotag.com/schemas/50add817-e7f1-4651-bd62-5471b2f5918f",
            ),
            "schema_current_address": icp.get_param(
                "ndi.schema_current_address",
                "https://dev-schema.ngotag.com/schemas/c4f4e15f-caf2-45be-8848-c9694db78418"
            ),
        }

    def _headers(self, access_token):
        return {
            "accept": "*/*",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @http.route(
        "/ndi/login/create-proof",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def ndi_login_create_proof(self, **kwargs):

        config = self._get_ndi_config()

        if not config["access_token"]:
            return Response(
                json.dumps({"ok": False, "error": "Missing ndi.access_token"}),
                content_type="application/json",
                status=500,
            )

        if not config["webhook_id"]:
            return Response(
                json.dumps({"ok": False, "error": "Missing ndi.webhook_id"}),
                content_type="application/json",
                status=500,
            )

        flow_type = request.session.get("ndi_flow_type") or "login"

        if flow_type not in ("login", "checkout_verify"):
            flow_type = "login"
            request.session["ndi_flow_type"] = "login"

        user = request.env.user

        is_logged_in_user = user and not user._is_public()
        is_linked_ndi_user = is_logged_in_user and bool(user.ndi_cid)
        is_checkout_flow = flow_type == "checkout_verify"

        if is_checkout_flow and is_linked_ndi_user:
            proof_payload = {
                "proofName": "Checkout Verification",
                "purpose": "login",
                "authenticationLevel": "Standard",
                "autoAcceptProof": "true",
                "proofAttributes": [
                    {
                        "name": "ID Number",
                        "restrictions": [{"schema_name": config["schema_name"]}],
                    }
                ],
            }
        else:
            proof_payload = {
                "proofName": "Foundational ID",
                "purpose": "login",
                "authenticationLevel": "Standard",
                "autoAcceptProof": "true",
                "proofAttributes": [
                    {"name": "ID Number", "restrictions": [{"schema_name": config["schema_name"]}]},
                    {"name": "Full Name", "restrictions": [{"schema_name": config["schema_name"]}]},
                    {"name": "Mobile Number", "restrictions": [{"schema_name": config["schema_mobile_number"]}]},
                    {"name": "Email", "restrictions": [{"schema_name": config["schema_email"]}]},
                    {"name": "Street", "restrictions": [{"schema_name": config["schema_current_address"]}]},
                    {"name": "City", "restrictions": [{"schema_name": config["schema_current_address"]}]},
                    {"name": "State", "restrictions": [{"schema_name": config["schema_current_address"]}]},
                    {"name": "Country", "restrictions": [{"schema_name": config["schema_current_address"]}]},
                    {"name": "Postal Code", "restrictions": [{"schema_name": config["schema_current_address"]}]},
                ],
            }

        proof_resp = requests.post(
            f"{config['base_url']}/verifier/v1/proof-request",
            headers=self._headers(config["access_token"]),
            json=proof_payload,
            timeout=30,
        )

        proof_data = proof_resp.json()

        data = proof_data.get("data", {})
        proof_request_url = data.get("proofRequestURL")
        deep_link_url = data.get("deepLinkURL")
        proof_thread_id = data.get("proofRequestThreadId")

        subscribe_payload = {
            "webhookId": config["webhook_id"],
            "threadId": proof_thread_id,
        }

        requests.post(
            f"{config['base_url']}/webhook/v1/subscribe",
            headers=self._headers(config["access_token"]),
            json=subscribe_payload,
            timeout=30,
        )

        request.session["ndi_proof_thread_id"] = proof_thread_id
        request.session["ndi_proof_request_url"] = proof_request_url

        attempt_vals = {
            "thread_id": proof_thread_id,
            "session_sid": request.session.sid,
            "status": "pending",
            "flow_type": flow_type,
        }

        if is_checkout_flow and is_logged_in_user:
            attempt_vals["user_id"] = user.id

        request.env["ndi.proof.login.attempt"].sudo().create(attempt_vals)

        return Response(
            json.dumps({
                "ok": True,
                "proof_request_url": proof_request_url,
                "deep_link_url": deep_link_url,
                "proof_thread_id": proof_thread_id,
                "qr_src": "/ndi/login/qr",
            }),
            content_type="application/json",
            status=200,
        )

    @http.route("/ndi/login", type="http", auth="public", website=True)
    def ndi_login_page(self, **kwargs):
        return request.render("website_ndi_integration.ndi_login_page")

    @http.route("/ndi/login/qr", type="http", auth="public", methods=["GET"], website=True)
    def ndi_login_qr(self, **kwargs):

        proof_request_url = request.session.get("ndi_proof_request_url")

        if not proof_request_url:
            return Response("No proof request URL found in session", status=404)

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(proof_request_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return request.make_response(
            buffer.getvalue(),
            headers=[("Content-Type", "image/png")],
        )

    @http.route(
        "/ndi/login/status",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def ndi_login_status(self, **kwargs):

        thread_id = request.session.get("ndi_proof_thread_id")

        if not thread_id:
            return {"status": "missing"}

        attempt = request.env["ndi.proof.login.attempt"].sudo().search(
            [("thread_id", "=", thread_id)],
            limit=1,
        )

        if not attempt:
            return {"status": "missing"}

        if attempt.status == "validated":

            flow_type = attempt.flow_type or "login"

            is_new_user = False
            is_first_bind = False

            try:
                raw_data = json.loads(attempt.raw_payload or "{}")
                is_new_user = raw_data.get("is_new_user", False)
                is_first_bind = raw_data.get("is_first_bind", False)
            except Exception:
                pass

            request.session["ndi_proof_thread_id"] = False
            request.session["ndi_proof_request_url"] = False

            attempt.write({"status": "used"})

            # Checkout verification (never login)
            if flow_type == "checkout_verify":
                return {
                    "status": "validated",
                    "redirect_url": "/shop/checkout",
                    "message": (
                        "NDI linked and verification successful."
                        if is_first_bind
                        else "Verification successful."
                    ),
                }

            # Login flow
            if not attempt.user_id:
                return {
                    "status": "pending",
                    "message": "Registration completed. Finalizing login...",
                }

            user = attempt.user_id.sudo()

            request.session.uid = user.id
            request.session.login = user.login
            request.session.session_token = user._compute_session_token(request.session.sid)

            return {
                "status": "validated",
                "redirect_url": "/",
                "message": (
                    "Registration completed. Finalizing login..."
                    if is_new_user
                    else "Login successful. Redirecting..."
                ),
            }

        if attempt.status == "rejected":
            return {"status": "rejected"}

        if attempt.status == "error":

            message = "Verification failed"

            try:
                raw_data = json.loads(attempt.raw_payload or "{}")
                message = raw_data.get("processing_error") or message
            except Exception:
                pass

            return {
                "status": "error",
                "message": message,
            }

        return {"status": "pending"}
