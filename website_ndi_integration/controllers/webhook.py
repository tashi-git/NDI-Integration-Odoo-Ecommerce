import json
import logging
import secrets
import string

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class NDIWebhookController(http.Controller):

    def _extract_attr(self, attrs_dict, key):
        try:
            values = attrs_dict.get(key) or []
            if values and isinstance(values, list):
                return values[0].get("value")
        except Exception:
            pass
        return False

    def _generate_login(self, cid, mobile, email):
        if email:
            return email.strip().lower()
        if mobile:
            return mobile.strip()
        return f"ndi_{cid}"

    def _generate_password(self, length=20):
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _update_user_and_partner(
        self,
        user,
        full_name,
        mobile,
        email,
        cid,
        street=False,
        city=False,
        state_name=False,
        country_name=False,
        zip_code=False,
    ):
        user = user.sudo()

        user_vals = {
            "ndi_verified": True,
        }

        if cid and not user.ndi_cid:
            user_vals["ndi_cid"] = cid

        if full_name and not user.name:
            user_vals["name"] = full_name

        if email and not user.email:
            user_vals["email"] = email

        user.write(user_vals)

        partner = user.partner_id
        partner_vals = {}

        if full_name and not partner.name:
            partner_vals["name"] = full_name

        if email and not partner.email:
            partner_vals["email"] = email

        if mobile:
            if not partner.phone:
                partner_vals["phone"] = mobile
            if "mobile" in partner._fields and not partner.mobile:
                partner_vals["mobile"] = mobile

        if street and not partner.street:
            partner_vals["street"] = street

        if city and not partner.city:
            partner_vals["city"] = city

        if zip_code and not partner.zip:
            partner_vals["zip"] = zip_code

        Country = request.env["res.country"].sudo()
        State = request.env["res.country.state"].sudo()

        country = partner.country_id or False

        if country_name and not partner.country_id:
            country = Country.search([("name", "ilike", country_name)], limit=1)
            if country:
                partner_vals["country_id"] = country.id

        if state_name and not partner.state_id:
            state_domain = [("name", "ilike", state_name)]
            if country:
                state_domain.append(("country_id", "=", country.id))

            state = State.search(state_domain, limit=1)
            if state:
                partner_vals["state_id"] = state.id

        if partner_vals:
            partner.sudo().write(partner_vals)

    def _find_or_create_user(
        self,
        cid,
        full_name,
        mobile,
        email,
        street=False,
        city=False,
        state_name=False,
        country_name=False,
        zip_code=False,
    ):
        Users = request.env["res.users"].sudo()

        user = Users.search([("ndi_cid", "=", cid)], limit=1)
        if user:
            self._update_user_and_partner(
                user,
                full_name,
                mobile,
                email,
                cid,
                street,
                city,
                state_name,
                country_name,
                zip_code,
            )
            return user, False

        if email:
            user = Users.search([("login", "=", email.strip().lower())], limit=1)
            if user:
                self._update_user_and_partner(
                    user,
                    full_name,
                    mobile,
                    email,
                    cid,
                    street,
                    city,
                    state_name,
                    country_name,
                    zip_code,
                )
                return user, False

        login = self._generate_login(cid, mobile, email)

        if Users.search([("login", "=", login)], limit=1):
            login = f"ndi_{cid}"

        password = self._generate_password()

        user_vals = {
            "name": full_name or f"NDI User {cid}",
            "login": login,
            "password": password,
            "ndi_cid": cid,
            "ndi_verified": True,
        }

        if email:
            user_vals["email"] = email

        user = Users.create(user_vals)

        portal_group = request.env.ref("base.group_portal")

        user.sudo().write({
            "group_ids": [(6, 0, [portal_group.id])]
        })

        self._update_user_and_partner(
            user,
            full_name,
            mobile,
            email,
            cid,
            street,
            city,
            state_name,
            country_name,
            zip_code,
        )

        return user, True

    @http.route("/ndi/webhook", type="http", auth="public", methods=["POST"], csrf=False)
    def ndi_webhook(self, **kwargs):
        try:
            payload = json.loads(request.httprequest.data.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        _logger.info("NDI webhook payload: %s", payload)

        event_type = payload.get("type")
        thread_id = payload.get("thid")

        if not thread_id:
            return Response(status=202)

        attempt = request.env["ndi.proof.login.attempt"].sudo().search(
            [("thread_id", "=", thread_id)],
            limit=1,
        )

        if not attempt:
            return Response(status=202)

        vals = {
            "raw_payload": json.dumps(payload),
        }

        if event_type == "present-proof/rejected":
            vals["status"] = "rejected"
            attempt.write(vals)
            return Response(status=202)

        if event_type == "present-proof/presentation-result":
            if payload.get("verification_result") != "ProofValidated":
                vals["status"] = "error"
                attempt.write(vals)
                return Response(status=202)

            requested_presentation = payload.get("requested_presentation") or {}
            revealed_attrs = requested_presentation.get("revealed_attrs") or {}
            self_attested_attrs = requested_presentation.get("self_attested_attrs") or {}

            cid = self._extract_attr(revealed_attrs, "ID Number")
            full_name = self._extract_attr(revealed_attrs, "Full Name")
            mobile = self._extract_attr(revealed_attrs, "Mobile Number") or \
                     self._extract_attr(self_attested_attrs, "Mobile Number")

            email = self._extract_attr(revealed_attrs, "Email") or \
                    self._extract_attr(self_attested_attrs, "Email")

            street = self._extract_attr(revealed_attrs, "Street") or \
                     self._extract_attr(self_attested_attrs, "Street")

            city = self._extract_attr(revealed_attrs, "City") or \
                   self._extract_attr(self_attested_attrs, "City")

            state_name = self._extract_attr(revealed_attrs, "State") or \
                         self._extract_attr(self_attested_attrs, "State")

            country_name = self._extract_attr(revealed_attrs, "Country") or \
                           self._extract_attr(self_attested_attrs, "Country")

            zip_code = self._extract_attr(revealed_attrs, "Postal Code") or \
                       self._extract_attr(self_attested_attrs, "Postal Code")

            if not cid:
                vals["status"] = "error"
                attempt.write(vals)
                return Response(status=202)

            try:
                flow_type = attempt.flow_type or "login"
                is_first_bind = False

                if flow_type == "checkout_verify":
                    user = attempt.user_id.sudo()

                    if not user:
                        raise ValueError("No logged-in user linked to checkout verification attempt")

                    Users = request.env["res.users"].sudo()

                    existing_user = Users.search([
                        ("ndi_cid", "=", cid),
                        ("id", "!=", user.id),
                    ], limit=1)

                    if existing_user:
                        raise ValueError("This Bhutan NDI wallet is already linked to another account")

                    if not user.ndi_cid:
                        user.write({
                            "ndi_cid": cid,
                            "ndi_verified": True,
                        })
                        is_first_bind = True
                    else:
                        if user.ndi_cid != cid:
                            raise ValueError("This NDI wallet does not match the logged-in account")

                        user.write({
                            "ndi_verified": True,
                        })
                        is_first_bind = False

                    self._update_user_and_partner(
                        user,
                        full_name,
                        mobile,
                        email,
                        cid,
                        street,
                        city,
                        state_name,
                        country_name,
                        zip_code,
                    )

                    is_new_user = False

                else:
                    user, is_new_user = self._find_or_create_user(
                        cid,
                        full_name,
                        mobile,
                        email,
                        street,
                        city,
                        state_name,
                        country_name,
                        zip_code,
                    )

                vals.update({
                    "status": "validated",
                    "cid": cid,
                    "full_name": full_name,
                    "mobile": mobile,
                    "email": email,
                    "user_id": user.id,
                    "raw_payload": json.dumps({
                        "payload": payload,
                        "is_new_user": is_new_user,
                        "flow_type": flow_type,
                        "is_first_bind": is_first_bind if flow_type == "checkout_verify" else False,
                    }),
                })

                attempt.write(vals)
                request.env.cr.commit()

            except Exception as e:
                _logger.exception("Failed processing NDI validated proof")
                vals["status"] = "error"
                vals["raw_payload"] = json.dumps({
                    "payload": payload,
                    "processing_error": str(e),
                })
                attempt.write(vals)

        return Response(status=202)
