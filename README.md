# Genesys Deckbuilder

Minor client modifications to support the Genesys point system in the EDOPro deckbuilder.

**NOTE**: Supporting Genesys deckbuilding is the only intended purpose of this client. This means that:
 - it is meant to be used alongside the original client, and is not a substitute for it.
 - every functionality outside the deckbuilder screen is untested and unsupported.

In short, use this client to build, and the original client to play.

## Installation

Every mentioned path is relative to your preexisting edopro installation (the folder where you have your `EDOPro` executable).

- Generate the banlist file with `update_genesys_banlist.py` and move the generated `genesys.lflist.conf` inside `/lflists`.
- Add the these lines to `/config/strings.conf`:

```
!system 3315 Points:
!system 3316 Stats:
```

- Compile this project following the [instructions](https://github.com/edo9300/edopro/wiki/1.-Prerequisites) of the main project.
- Take the `ygopro` executable and place it in the same directory as the `EDOPro` executable.
