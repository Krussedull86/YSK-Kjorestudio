# YSK Kjørestudio

Lokal klasseromsvisning på Windows og Android-registrering ute i bilen. Supabase samler turer fra lærere med egne kontoer.

Versjon **1.3.2 / bygg 6** har hvit klasseromsvisning, elleve statistikkvalg, elevgrafer, tur 1–5 og dev/stable per bruker. Fullskjerm velges på skjerm 1 eller 2. Rangering sammenligner samme kurs, bil og turnummer.

## Bruk

Installer APK over eksisterende app. Kjør den separate `YSK_Kjorestudio.exe` på Windows uten Python. Kildepakken kan også kjøres med `Start.bat`. `Start_Demo.bat` viser demodata. Les `LES_MEG.txt` for registrering, oppdateringer og teststatus.

## Oppdateringer

`.github/workflows/dev.yml` er klargjort for Windows- og Android-bygg, tester og dev-publisering. Admin velger testere i brukerlisten. Stable fremmes uttrykkelig i den innloggede portalen med samme releasefiler. Android krever bekreftelse på installasjon.

GitHub-repoet er offentlig. GitHub Actions bygger og signerer APK og EXE automatisk ved push til dev. Android-nøkkelen og passordene er krypterte Actions-secrets. Versjon 1.3.2 bygg 6 er publisert til Supabase dev-kanalen og kontrollert med SHA-256. Alle 35 tester består på Windows. Stable er urørt. Portalen er ikke hostet ennå.


## Utvikling

```sh
python -m unittest discover -v
node cloud/functions/ysk-admin/test.mjs
node cloud/functions/ysk-admin/test_updates.mjs
node cloud/functions/ysk-publish/test.mjs
```

Android bygges med JDK 17 og SDK 35 gjennom `android/build_android.py`. Windows EXE bygges med PyInstaller på Windows. Private signing-filer, databaser og innloggingsøkter skal aldri inn i GitHub. Behold samme Android-signering for å oppdatere appen uten å miste lokale data.
