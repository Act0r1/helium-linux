# Helium Spaces

This is [Helium](https://github.com/imputnet/helium), slightly modified to
add Zen-style workspaces. Everything else is plain Helium.

> [!NOTE]
> This is an unofficial fork. Please report bugs here, not to Helium.

## What's different
- **Workspaces** in the vertical tab strip: a workspace header above the tabs
  and an icon strip at the bottom of the sidebar, like in Zen.
- Each workspace keeps its own tabs. Pinned tabs are shared across all
  workspaces.
- Every workspace has a name, emoji icon and color. Workspaces are restored
  with the session.
- In horizontal tab mode all tabs are shown, as in regular Helium.
- The built-in password manager is enabled again.

All changes live in [`patches/helium-ws/`](patches/helium-ws).

## Credits

### Helium
All the real work is [Helium](https://github.com/imputnet/helium) by
[imput](https://github.com/imputnet). This repo only adds workspaces on top.

### ungoogled-chromium
This repo uses some stuff that originally came from
[ungoogled-chromium-portablelinux](https://github.com/ungoogled-software/ungoogled-chromium-portablelinux)
before we fully remade it and forked it for Helium.

## License
All code, patches, modified portions of imported code or patches, and
any other content that is unique to Helium and not imported from other
repositories is licensed under GPL-3.0. See [LICENSE](LICENSE).

Any content imported from other projects retains its original license (for
example, any original unmodified code imported from ungoogled-chromium remains
licensed under their [BSD 3-Clause license](LICENSE.ungoogled_chromium)).

## Building
To build Helium Spaces, run `scripts/docker-build.sh` from the repo root.

The `scripts/docker-build.sh` script will:
1. Create a Docker image of a Debian-based building environment with all
   required packages (llvm, nodejs and distro packages) included.
2. Run `scripts/build.sh` inside the Docker image to build Helium.

Running `scripts/build.sh` directly will not work unless you're running a
Debian-based distro and have all necessary dependencies installed. This repo is
designed to avoid having to configure the building environment on your Linux
installation.

### Packaging
After building, run `scripts/package.sh`. Alternatively, you can run
`package/docker-package.sh` to build inside a Docker image. Either of these
scripts will create `tar.xz` and `AppImage` files under `build/`.

If you would like to also generate a .deb file, you can set `MAKE_DEB=1` when
running the release script.

### Development
By default, the build script uses tarball. If you need to use a source tree
clone, you can run `scripts/docker-build.sh -c` instead. This may be useful if
a tarball for a release isn't available yet.

