from odoo import models, fields


class NDIProofLoginAttempt(models.Model):
    _name = "ndi.proof.login.attempt"
    _description = "NDI Proof Login Attempt"
    _rec_name = "thread_id"

    thread_id = fields.Char(required=True, index=True)
    session_sid = fields.Char(index=True)

    status = fields.Selection([
        ("pending", "Pending"),
        ("validated", "Validated"),
        ("rejected", "Rejected"),
        ("error", "Error"),
        ("used", "Used"),
    ], default="pending", required=True)

    cid = fields.Char(string="CID", index=True)
    full_name = fields.Char()
    mobile = fields.Char()
    email = fields.Char()

    user_id = fields.Many2one("res.users")

    flow_type = fields.Selection([
        ("login", "Login"),
        ("checkout_verify", "Checkout Verification"),
    ], default="login", required=True)

    raw_payload = fields.Text()
