# -*- encoding: utf-8 -*-

{
    'name': 'XIM FEL Guatemala',
    'version': '16.0.0.0.2',
    'category': 'Invoicing',
    'summary': 'Módulo Certificar en Guatemala-SAT',
    'description': """ 
# **Certificación SAT Guatemala por I3 y Felplex**

Este módulo está diseñado para facilitar la certificación ante la **Superintendencia de Administración Tributaria (SAT)** de Guatemala directamente desde **Odoo**. Con esta herramienta, las empresas pueden emitir **Documentos Tributarios Electrónicos (DTE)** de prueba, asegurando que cumplen con los requisitos establecidos por la SAT para la facturación electrónica.

## **Características principales:**

- ### **📄 Diario Preconfigurado**
  - El módulo crea un diario específico llamado **`FACT FELPLEX/I3`**, el cual está completamente configurado y listo para ser utilizado por un certificador autorizado para emitir hasta **5 DTE de prueba**.

                    """,
    'author': 'Integración Inteligente de Información S.A.',
    'website': 'www.xim.technology',
    'support': 'info@ximdatacenter.com',
    'maintainer': 'I3',
    'license': 'OPL-1',
    'category': 'Accounting',
    'images': ['static/description/images/new_banner.gif'],
    'depends': ['account', 'l10n_gt'],
    'data': [
        'views/account_move_view.xml', 
        'views/journal_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
