{
    "name": "Website NDI Integration",
    "version": "19.0.1.0.0",
    "author": "Tashi Wangchuk",
    "license": "LGPL-3",
    "depends": ["web", "website", "auth_signup", "portal"],
    "data": [
        "views/ndi_login.xml",
        "views/ndi_login_page.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "website_ndi_integration/static/src/css/ndi_login.css",
        ],
    },
    "installable": True,
    "application": False,
}
