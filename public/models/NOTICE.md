# Commander asset sources and notices

Yukimura and Ieyasu incorporate modified continuous arm/hand geometry and full-body deformation bones derived from the MPFB / MakeHuman bundled base mesh, default rig, and skin weights, licensed CC0-1.0.

Upstream: https://github.com/makehumancommunity/mpfb2
Pinned commit: d0a32e57a7f915cb2f2b95410e2117648c7bbb7e

Source assets, upstream license text, and hashes are preserved in `assets/vendor/mpfb/` in this repository. The MPFB add-on code (GPL) was not imported into the game. The armor and gameplay animations are authored by this project; the asset license does not relicense the rest of the repository.

## Commander heads

Yukimura and Ieyasu also incorporate modified head geometry and skin textures from Microsoft Rocketbox Male_Adult_10, licensed MIT.

Upstream: https://github.com/microsoft/Microsoft-Rocketbox
Pinned commit: 0943055db6ec570bcef9f2c8b41c9e5467c808f9
Source asset path: `Assets/Avatars/Adults/Male_Adult_10`

The upstream copyright and permission notice is retained in [LICENSE-Rocketbox.txt](LICENSE-Rocketbox.txt). Repository source records are in `assets/research/character-candidates/`.

## Current integration

As of 2026-10-14, the game uses the v22 commanders: the v21 menpo shape and project-authored v22 weapon grip animations. Shared armor and animation controls are project-authored; third-party asset licenses do not relicense the whole game. See [current status](../../docs/STATUS.md) and [model workflow](../../docs/MODELS.md) in the source repository. Those documentation paths are repository links, not published Pages routes.
