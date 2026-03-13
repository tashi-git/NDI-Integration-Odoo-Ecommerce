from odoo import models, fields


class ResUsers(models.Model):
    _inherit = "res.users"

    # Verified Bhutan NDI CID used as the main identity key
    ndi_cid = fields.Char(string="NDI CID", index=True, copy=False)

    # Marks that the user was verified through Bhutan NDI
    ndi_verified = fields.Boolean(string="NDI Verified", default=False, copy=False)
