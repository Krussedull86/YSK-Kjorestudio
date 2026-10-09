# YSK Kjørestudio

Lokal klasseromsvisning på Windows og Android-registrering ute i bilen. Supabase samler turer fra lærere med egne kontoer.

Versjon **1.5.0 / bygg 8** har hvit klasseromsvisning, elleve statistikkvalg, elevgrafer, tur 1–5 og dev/stable per bruker. Fullskjerm velges på skjerm 1 eller 2. Rangering sammenligner samme kurs, bil og turnummer.

## Bruk

Installer APK over eksisterende app. Kjør den separate `YSK_Kjorestudio.exe` på Windows uten Python. Kildepakken kan også kjøres med `Start.bat`. `Start_Demo.bat` viser demodata. Les `LES_MEG.txt` for registrering, oppdateringer og teststatus.

## Telefon og tidtaking

Én liten menylinje; status og innhold ruller, uten fast bunn. Tidtakeren ligger øverst i registreringen. **Start** fyller inn dato/starttid; **Stopp** fyller inn kjøretid. **Fortsett** gjenopptar samme måling. Meny → **Fortsett tur** åpner utkastet etter appbytte. Tidtakingen fortsetter med skjermen av. Nullstilling av klokken beholder manuelt registrert tid. Stopp før lagring.

## Distribusjon (dev 1.9.0)

Admin velger **Kursoppsett** på PC eller under **Turer, kurs og biler → Kurs** på Android. Angi antall aktive turer slik at tur 4 er aktiv, **antall distribusjonsstopp (1–30)** og **forventet totaltid i minutter**. 0 stopp slår av stoppplanen. Forventet totaltid vises kun som informasjon.

Android: velg sjåfør, kurs, bil og **Transportoppdrag 1 (distribusjon)**. Trykk **Start distribusjonsoppdrag**, deretter **Rygget til rampe** eller **Avbryt stopp** for hvert stopp. Avbrudd kan ha en grunn. **Rygget til rampe** og **Avbryt stopp** finnes også i appmenyen og i Androids nedtrekkbare tidtakingsvarsel. I varselet registreres avbrudd uten grunn; du kan bruke skjemaet for å angi grunn. Etter alle stopp vises **Avslutt**. Klokken inkluderer lasting, venting og pauser og fortsetter mens appen er lukket. Meny → **Fortsett tur** gjenåpner utkastet. Etter alle stopp: **Avslutt distribusjonsoppdrag**, fyll øvrige målinger/vurderinger og **Lagre tur**. Tidsplanen kopieres ved Start og endres ikke av senere kursendringer.

Stopploggen viser tid siden forrige registrerte stopp, totalt fra start, status for hvert stopp. Avbrutte stopp beholdes i loggen og teller ikke som gjennomførte leveringsstopp. **Unødige stopp** er en separat måling. På PC: åpne turen og velg **Vis distribusjonsstopp**, eller bruk stopptabellen fra elevdetaljene i klasseromsvisningen/storskjermen.

## Rediger og slett

Android: **Mine turer → Administrer turer, kurs og biler**. PC: fanen **Turer, kurs og biler → Hent fra sky**. Velg tur, kurs eller bil og bruk redigering eller sletting. Kurs-/bilnavn endres på alle aktive tilhørende turer. Sletting av kurs eller bil flytter tilhørende turer til papirkurven, med antallet vist før bekreftelse. Turene kan gjenopprettes enkeltvis.

Lærere endrer egne turer. Admin administrerer alle skolens turer og kurs/biler. PC-endringer synkroniseres tilbake til Android. Gamle offline-utkast kan ikke overskrive en nyere skyversjon. Oppdater både APK og EXE. Les `LES_MEG_REDIGERING.txt`.

## Oppdateringer

`.github/workflows/dev.yml` er klargjort for Windows- og Android-bygg, tester og dev-publisering. Admin velger testere i brukerlisten. Stable fremmes uttrykkelig i den innloggede portalen med samme releasefiler. Android krever bekreftelse på installasjon.

GitHub-repoet er offentlig. GitHub Actions bygger og signerer APK og EXE automatisk ved push til dev. Android-nøkkelen og passordene er krypterte Actions-secrets. Versjon 1.5.0 bygg 8 er publisert til Supabase dev-kanalen og kontrollert med SHA-256. Alle 38 PC-tester og tidtakerens Java-tester består. Stable er urørt. Portalen er ikke hostet ennå.


## Utvikling

```sh
python -m unittest discover -v
node cloud/functions/ysk-admin/test.mjs
node cloud/functions/ysk-admin/test_updates.mjs
node cloud/functions/ysk-admin/test_trips.mjs
node cloud/functions/ysk-publish/test.mjs
```

Android bygges med JDK 17 og SDK 35 gjennom `android/build_android.py`. Windows EXE bygges med PyInstaller på Windows. Private signing-filer, databaser og innloggingsøkter skal aldri inn i GitHub. Behold samme Android-signering for å oppdatere appen uten å miste lokale data.

### Separate dev-oppdateringer
Windows-filer bygger bare Windows; filer under `android/` bygger bare Android. Felles sky- og byggeoppsett bygger begge. Dokumentasjon alene starter ingen bygg. I GitHub Actions → YSK dev → Run workflow kan du velge `auto`, `windows`, `android` eller `both`. En push med `[windows-only]` eller `[android-only]` i siste commit-tittel velger eksplisitt bare den plattformen. Øk `BUILD` i `version.py` før en utgivelse; byggnummeret er en felles, stigende utgivelsessekvens. Android-manifestet får utgivelsens versjon under bygging. Plattformen som ikke publiseres beholder forrige oppdatering og versjon.

### Kursoppsett og sammenligning (dev)
Admin velger kursnavn og 1–5 aktive turer via Kursoppsett på PC eller Administrer → Kurs → Kursoppsett på Android. Turene aktiveres fra 1 til valgt antall; eksisterende registreringer beholdes. Gamle kurs har fem aktive turer. Kursoppsettet hentes ved synkronisering og er tilgjengelig uten nett etterpå. Windows kan også ha lokale kursoppsett uten skykonto. Klasserommet viser turenes navn; Sammenlign turer velger hvilke registreringer som inngår i historikken, og Sammenlign fra på storskjermen velger startturen.

## Skoler og avdelinger (dev 1.8.0)
Vanlige brukere logger inn med e-post og passord. Prosjektadresse og publishable key er innebygd; service key ligger kun på serveren. Oppstart viser innlogging og krever godkjent, aktiv konto før programmet åpnes. Etter godkjent innlogging er lokal lagring uten nett fortsatt tilgjengelig.

Under **Admin / lærere** kan admin opprette skoler, opprette avdelinger, endre navn og tildele en skole og valgfri avdeling når en bruker opprettes. Eksisterende brukere kan også tildeles skole/avdeling. Admin administrerer egen skole og nye skoler de selv oppretter. Ingen tilgang til andre skoler gis automatisk. Avdeling er tilhørighet innen skolen; kurs og klasserom deles på skolenivå.

Tidligere turer beholdes i opprinnelig skole. Administratorer kan få ny avdeling, men flyttes ikke mellom skoler; opprett en ny administratorkonto i den nye skolen. Etter skolebytte må lokale data holdes separat: PC og Android stopper synkronisering ved endret skoletilknytning, slik at gamle utkast ikke sendes til ny skole. Bruk en separat PC-database/Android-installasjon for ny skole.

## Påkrevd innlogging (dev 1.8.1)
PC-programmet bygger ikke registrerings-, admin- eller klasseromsvisning og starter ikke lokal mobilserver før serveren har godkjent kontoen. Android sperrer registrering, resultater, meny og tilbakeknapp før innlogging. Lagret kryptert økt kontrolleres automatisk ved oppstart; ugyldig økt gir ingen tilgang. Oppstart/kontokontroll krever nett. Etter innlogging kan lokale turer lagres mens nettet er borte. Logg ut returnerer til innlogging og beholder lokale turer og utkast.
