from datetime import timedelta
from odoo import http, fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleNDICheckoutVerification(WebsiteSale):

    def _is_ndi_user(self, user):

        two_minutes_ago = fields.Datetime.now() - timedelta(minutes=2)

        attempt = request.env["ndi.proof.login.attempt"].sudo().search([
            ("user_id", "=", user.id),
            ("status", "in", ["validated", "used"]),
            ("write_date", ">", two_minutes_ago),
        ], order="write_date desc", limit=1)

        return bool(attempt)

    @http.route("/shop/checkout", type="http", auth="public", website=True, sitemap=False)
    def shop_checkout(self, **post):

        user = request.env.user

        if user._is_public():
            return request.redirect("/ndi/login?redirect=/shop/checkout")

        if not self._is_ndi_user(user):
            return request.redirect("/ndi/login?redirect=/shop/checkout")

        return super().shop_checkout(**post)
