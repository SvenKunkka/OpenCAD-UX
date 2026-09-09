# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x (MVP) | :white_check_mark: |

## Reporting a vulnerability

OpenCAD UX is an add-on that runs *inside* FreeCAD with the same privileges as
FreeCAD itself. Please report security issues privately instead of opening a
public issue:

- open a **GitHub Security Advisory** at
  https://github.com/OpenCAD-UX/OpenCAD-UX/security/advisories/new, or
- email the maintainers (address published on the GitHub profile page).

Please include: FreeCAD version + OS, the add-on version, a minimal
reproduction, and the impact you observed.

## Scope & hardening notes

- The add-on never executes downloaded code; all commands resolve to FreeCAD
  standard commands or to code shipped in this repository.
- Reference-image import only reads image files you explicitly choose; it
  never writes outside your FreeCAD user data and the backup directories.
- Settings live in FreeCAD's own parameter store; installers back up the
  config files they touch and print a restore path.
- Malicious `.FCStd` files can always carry macros; OpenCAD UX does not add
  an extra macro execution surface on top of FreeCAD itself.
