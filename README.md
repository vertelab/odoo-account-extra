# odoo-account-extra — gren 19.0

> **Denna gren är avsiktligt tom.** Modulerna är INTE portade till Odoo 19.
> Grenen finns så att dev-miljöer (`hansolo19`) kan klona den utan att falla,
> men den påstår ingenting om att koden är portad.

## Baseline

| | |
|---|---|
| Källa | `14.0 (senaste versionsgren)` |
| Moduler | **3** |
| Grenar | `10.0`, `14.0`, `master`, `master10` |

## Moduler

- `account_invoice_image`
- `project_issue_account`
- `website_project_issue`

## Blockerare

**4 externa beroenden saknas:**

| Beroende | Behövs av |
|---|---|
| `account_invoice_image` | `project_issue_account` |
| `attachment_image` | `project_issue_account` |
| `attachment_pdf2image` | `website_project_issue` |
| `project_issue` | `project_issue_account` |

## Nästa steg

Portering sker på `*-pfile`-maskin med versionsagnostisk kod
(`.p.py` / `.p.xml`). Se `/skill:odoo-pfiles`.
