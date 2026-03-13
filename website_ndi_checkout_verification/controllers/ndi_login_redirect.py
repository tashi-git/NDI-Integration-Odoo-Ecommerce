import json

from odoo import http
from odoo.http import request

from odoo.addons.website_ndi_integration.controllers.ndi_login import NDILoginController


class NDILoginRedirectOverride(NDILoginController):

    @http.route("/ndi/login", type="http", auth="public", website=True)
    def ndi_login_page(self, **kwargs):
        redirect_url = kwargs.get("redirect")

        if redirect_url:
            request.session["ndi_login_redirect_url"] = redirect_url

            if redirect_url == "/shop/checkout" and not request.env.user._is_public():
                request.session["ndi_flow_type"] = "checkout_verify"
            else:
                request.session["ndi_flow_type"] = "login"

        return super().ndi_login_page(**kwargs)

    @http.route(
        "/ndi/login/create-proof",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def ndi_login_create_proof(self, **kwargs):
        result = super().ndi_login_create_proof(**kwargs)

        proof_thread_id = request.session.get("ndi_proof_thread_id")
        flow_type = request.session.get("ndi_flow_type") or "login"

        if proof_thread_id:
            attempt = request.env["ndi.proof.login.attempt"].sudo().search(
                [("thread_id", "=", proof_thread_id)],
                limit=1,
            )

            if attempt:
                vals = {
                    "flow_type": flow_type,
                }

                if flow_type == "checkout_verify" and not request.env.user._is_public():
                    vals["user_id"] = request.env.user.id

                attempt.write(vals)

        return result

    @http.route(
        "/ndi/login/status",
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def ndi_login_status(self, **kwargs):
        result = super().ndi_login_status(**kwargs)

        if isinstance(result, dict) and result.get("status") == "validated":
            redirect_url = request.session.get("ndi_login_redirect_url")

            if redirect_url:
                result["redirect_url"] = redirect_url

                if redirect_url == "/shop/checkout":
                    thread_id = request.session.get("ndi_proof_thread_id")
                    is_first_bind = False

                    if thread_id:
                        attempt = request.env["ndi.proof.login.attempt"].sudo().search(
                            [("thread_id", "=", thread_id)],
                            limit=1,
                        )
                        if attempt:
                            try:
                                raw_data = json.loads(attempt.raw_payload or "{}")
                                is_first_bind = raw_data.get("is_first_bind", False)
                            except Exception:
                                pass

                    result["message"] = (
                        "Identity verified and linked to your account. Redirecting to checkout..."
                        if is_first_bind
                        else "Verification successful. Redirecting to checkout..."
                    )
                else:
                    result["message"] = result.get("message") or "Login successful. Redirecting..."

                request.session["ndi_login_redirect_url"] = False
                request.session["ndi_flow_type"] = False

        return result
