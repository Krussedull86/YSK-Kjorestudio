# YSK Kjørestudio

Lokal klasseromsvisning på Windows og Android-registrering ute i bilen. Supabase samler turer fra lærere med egne kontoer.

Versjon **1.3.0 / bygg 4** har hvit klasseromsvisning, elleve statistikkvalg, elevgrafer, tur 1–5 og dev/stable per bruker. Fullskjerm velges på skjerm 1 eller 2. Rangering sammenligner samme kurs, bil og turnummer.

## Bruk

Installer APK over eksisterende app. Pakk ut PC-pakken og kjør `Start.bat`, eller bygg EXE med `Bygg_EXE.bat`. `Start_Demo.bat` viser demodata. Les `LES_MEG.txt` for registrering, oppdateringer og teststatus.

## Oppdateringer

`.github/workflows/dev.yml` er klargjort for Windows- og Android-bygg, tester og dev-publisering. Admin velger testere i brukerlisten. Stable fremmes uttrykkelig i den innloggede portalen med samme releasefiler. Android krever bekreftelse på installasjon.

GitHub-repo, Pages, private signeringssecrets og OIDC-publisher må først konfigureres som beskrevet i `release_portal/OPPSETT.txt`. Ingen CI-utgave er publisert ennå. Supabase-API og medlemskanaler er aktivert; stable er urørt.

## Utvikling

```sh
python -m unittest discover -v
node cloud/functions/ysk-admin/test.mjs
node cloud/functions/ysk-admin/test_updates.mjs
node cloud/functions/ysk-publish/test.mjs
```

Android bygges med JDK 17 og SDK 35 gjennom `android/build_android.py`. Windows EXE bygges med PyInstaller på Windows. Private signing-filer, databaser og innloggingsøkter skal aldri inn i GitHub. Behold samme Android-signering for å oppdatere appen uten å miste lokale data.
